"""Database persistence module using SQLite with WAL mode.
Stores virtual keys, monthly usage records, request telemetry logs, and cache entries.
"""

import json
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from prism.config import config, BASE_DIR

DB_PATH = BASE_DIR / "prism.db"


class Database:
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self._lock = threading.Lock()
        self.init_db()
        self.seed_tenants()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        conn.execute("PRAGMA busy_timeout=5000;")
        conn.execute("PRAGMA cache_size=-64000;")
        return conn

    def init_db(self):
        with self._lock:
            with self.get_connection() as conn:
                conn.execute("""
                CREATE TABLE IF NOT EXISTS tenants (
                    virtual_key TEXT PRIMARY KEY,
                    team TEXT NOT NULL,
                    monthly_budget_usd REAL NOT NULL,
                    requests_per_minute INTEGER NOT NULL,
                    tokens_per_minute INTEGER,
                    model_allowlist TEXT NOT NULL,
                    cache_enabled INTEGER NOT NULL,
                    similarity_threshold REAL,
                    status TEXT DEFAULT 'active',
                    created_at TEXT NOT NULL
                );
                """)

                conn.execute("""
                CREATE TABLE IF NOT EXISTS usage_records (
                    virtual_key TEXT NOT NULL,
                    year_month TEXT NOT NULL,
                    spend_usd REAL DEFAULT 0.0,
                    requests_count INTEGER DEFAULT 0,
                    prompt_tokens INTEGER DEFAULT 0,
                    completion_tokens INTEGER DEFAULT 0,
                    cache_hits INTEGER DEFAULT 0,
                    PRIMARY KEY (virtual_key, year_month)
                );
                """)

                conn.execute("""
                CREATE TABLE IF NOT EXISTS request_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    request_id TEXT NOT NULL,
                    virtual_key TEXT NOT NULL,
                    requested_model TEXT NOT NULL,
                    resolved_provider TEXT,
                    resolved_model TEXT,
                    status TEXT NOT NULL,
                    prompt_tokens INTEGER DEFAULT 0,
                    completion_tokens INTEGER DEFAULT 0,
                    cost_usd REAL DEFAULT 0.0,
                    cache_result TEXT DEFAULT 'miss',
                    fallback INTEGER DEFAULT 0,
                    route_reason TEXT,
                    retries INTEGER DEFAULT 0,
                    latency_ms INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL
                );
                """)

                conn.execute("""
                CREATE TABLE IF NOT EXISTS cache_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    virtual_key TEXT NOT NULL,
                    model TEXT NOT NULL,
                    prompt_text TEXT NOT NULL,
                    prompt_vector TEXT NOT NULL,
                    response_payload TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                """)

                # Production indexes for fast query resolution
                conn.execute("CREATE INDEX IF NOT EXISTS idx_logs_vkey ON request_logs(virtual_key, created_at);")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_cache_vkey ON cache_entries(virtual_key);")
                conn.commit()

    def seed_tenants(self):
        """Populates tenants from seed_keys.json if not present."""
        tenants = config.seed_keys.get("tenants", [])
        now_str = datetime.now(timezone.utc).isoformat()
        with self._lock:
            with self.get_connection() as conn:
                for t in tenants:
                    conn.execute("""
                    INSERT OR REPLACE INTO tenants (
                        virtual_key, team, monthly_budget_usd, requests_per_minute,
                        tokens_per_minute, model_allowlist, cache_enabled, similarity_threshold,
                        status, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        t["virtual_key"],
                        t["team"],
                        float(t["monthly_budget_usd"]),
                        int(t["rate_limit"]["requests_per_minute"]),
                        int(t["rate_limit"].get("tokens_per_minute", 100000)),
                        json.dumps(t["model_allowlist"]),
                        1 if t.get("semantic_cache", {}).get("enabled", False) else 0,
                        float(t.get("semantic_cache", {}).get("similarity_threshold", 0.85)),
                        "active",
                        now_str
                    ))
                conn.commit()

    def get_tenant(self, virtual_key: str) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.execute("SELECT * FROM tenants WHERE virtual_key = ?", (virtual_key,))
            row = cursor.fetchone()
            if not row:
                return None
            data = dict(row)
            data["model_allowlist"] = json.loads(data["model_allowlist"])
            data["cache_enabled"] = bool(data["cache_enabled"])
            return data

    def get_all_tenants(self) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.execute("SELECT * FROM tenants")
            result = []
            for row in cursor.fetchall():
                data = dict(row)
                data["model_allowlist"] = json.loads(data["model_allowlist"])
                data["cache_enabled"] = bool(data["cache_enabled"])
                result.append(data)
            return result

    @staticmethod
    def get_current_year_month() -> str:
        return datetime.now(timezone.utc).strftime("%Y-%m")

    def get_monthly_spend(self, virtual_key: str, year_month: Optional[str] = None) -> float:
        ym = year_month or self.get_current_year_month()
        with self.get_connection() as conn:
            cursor = conn.execute(
                "SELECT spend_usd FROM usage_records WHERE virtual_key = ? AND year_month = ?",
                (virtual_key, ym)
            )
            row = cursor.fetchone()
            return float(row["spend_usd"]) if row else 0.0

    def record_usage(
        self,
        virtual_key: str,
        prompt_tokens: int,
        completion_tokens: int,
        cost_usd: float,
        is_cache_hit: bool = False
    ):
        ym = self.get_current_year_month()
        with self._lock:
            with self.get_connection() as conn:
                conn.execute("""
                INSERT INTO usage_records (
                    virtual_key, year_month, spend_usd, requests_count,
                    prompt_tokens, completion_tokens, cache_hits
                ) VALUES (?, ?, ?, 1, ?, ?, ?)
                ON CONFLICT(virtual_key, year_month) DO UPDATE SET
                    spend_usd = spend_usd + excluded.spend_usd,
                    requests_count = requests_count + 1,
                    prompt_tokens = prompt_tokens + excluded.prompt_tokens,
                    completion_tokens = completion_tokens + excluded.completion_tokens,
                    cache_hits = cache_hits + excluded.cache_hits
                """, (
                    virtual_key, ym, float(cost_usd),
                    int(prompt_tokens), int(completion_tokens),
                    1 if is_cache_hit else 0
                ))
                conn.commit()

    def log_request(
        self,
        request_id: str,
        virtual_key: str,
        requested_model: str,
        resolved_provider: Optional[str],
        resolved_model: Optional[str],
        status: str,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        cost_usd: float = 0.0,
        cache_result: str = "miss",
        fallback: bool = False,
        route_reason: Optional[str] = None,
        retries: int = 0,
        latency_ms: int = 0
    ):
        now_str = datetime.now(timezone.utc).isoformat()
        with self._lock:
            with self.get_connection() as conn:
                conn.execute("""
                INSERT INTO request_logs (
                    request_id, virtual_key, requested_model, resolved_provider,
                    resolved_model, status, prompt_tokens, completion_tokens,
                    cost_usd, cache_result, fallback, route_reason, retries,
                    latency_ms, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    request_id, virtual_key, requested_model, resolved_provider,
                    resolved_model, status, int(prompt_tokens), int(completion_tokens),
                    float(cost_usd), cache_result, 1 if fallback else 0,
                    route_reason, int(retries), int(latency_ms), now_str
                ))
                conn.commit()

    def get_logs(self, virtual_key: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            if virtual_key:
                cursor = conn.execute(
                    "SELECT * FROM request_logs WHERE virtual_key = ? ORDER BY id DESC LIMIT ?",
                    (virtual_key, limit)
                )
            else:
                cursor = conn.execute(
                    "SELECT * FROM request_logs ORDER BY id DESC LIMIT ?",
                    (limit,)
                )
            return [dict(row) for row in cursor.fetchall()]

    def get_usage_summary(
        self,
        virtual_key: str,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """Calculates accurate usage for virtual_key across requested date window."""
        with self.get_connection() as conn:
            query = "SELECT * FROM request_logs WHERE virtual_key = ?"
            params: List[Any] = [virtual_key]
            if from_date:
                query += " AND created_at >= ?"
                params.append(from_date)
            if to_date:
                query += " AND created_at <= ?"
                params.append(to_date)

            cursor = conn.execute(query, params)
            rows = cursor.fetchall()

            requests = len(rows)
            prompt_tokens = sum(r["prompt_tokens"] for r in rows)
            completion_tokens = sum(r["completion_tokens"] for r in rows)
            cost_usd = sum(r["cost_usd"] for r in rows)
            cache_hits = sum(1 for r in rows if r["cache_result"] == "hit")

            return {
                "key": virtual_key,
                "from": from_date or "",
                "to": to_date or "",
                "requests": requests,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "cost_usd": round(cost_usd, 6),
                "cache_hits": cache_hits
            }

    def get_cache_stats(self) -> Dict[str, Any]:
        with self.get_connection() as conn:
            cursor = conn.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN cache_result = 'hit' THEN 1 ELSE 0 END) as hits,
                SUM(CASE WHEN cache_result = 'miss' THEN 1 ELSE 0 END) as misses
            FROM request_logs
            WHERE status IN ('ok', 'cache_hit')
            """)
            row = cursor.fetchone()
            total = (row["total"] or 0)
            hits = (row["hits"] or 0)
            misses = (row["misses"] or 0)
            hit_rate = (hits / total) if total > 0 else 0.0
            return {
                "total_requests": total,
                "hits": hits,
                "misses": misses,
                "hit_rate": round(hit_rate, 4)
            }


db = Database()
