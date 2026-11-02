#!/usr/bin/env python3
"""All-in-one local development and demo runner for Prism.
Launches:
  1. Mock Provider Alpha (port 9001)
  2. Mock Provider Beta  (port 9002)
  3. Prism Gateway       (port 8080)
Gracefully terminates all child processes on Ctrl+C or SIGTERM.
"""

import os
import signal
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable


def wait_for_ready(url, timeout=15):
    start = time.time()
    while time.time() - start < timeout:
        try:
            with urllib.request.urlopen(url, timeout=1) as resp:
                if resp.status == 200:
                    return True
        except Exception:
            pass
        time.sleep(0.4)
    return False


def main():
    print("=" * 64)
    print("  Starting Prism: LLM Gateway & Semantic Cache")
    print("=" * 64)

    procs = []

    def cleanup(signum=None, frame=None):
        print("\nShutting down all servers...")
        for p in procs:
            if p.poll() is None:
                p.terminate()
        for p in procs:
            try:
                p.wait(timeout=2)
            except subprocess.TimeoutExpired:
                p.kill()
        print("All servers stopped cleanly.")
        sys.exit(0)

    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    # 1. Start Mock Provider Alpha
    print("-> Starting Provider Alpha on port 9001...")
    alpha_proc = subprocess.Popen([
        PYTHON, str(ROOT / "scripts" / "mock_provider.py"),
        "--port", "9001", "--name", "alpha"
    ])
    procs.append(alpha_proc)

    # 2. Start Mock Provider Beta
    print("-> Starting Provider Beta on port 9002...")
    beta_proc = subprocess.Popen([
        PYTHON, str(ROOT / "scripts" / "mock_provider.py"),
        "--port", "9002", "--name", "beta"
    ])
    procs.append(beta_proc)

    # 3. Start Prism Gateway
    print("-> Starting Prism Gateway on port 8080...")
    gateway_proc = subprocess.Popen([
        PYTHON, str(ROOT / "main.py"),
        "--port", "8080"
    ])
    procs.append(gateway_proc)

    # Wait for gateway and providers to be ready
    print("\nWaiting for services to become healthy...")
    alpha_ready = wait_for_ready("http://127.0.0.1:9001/health")
    beta_ready = wait_for_ready("http://127.0.0.1:9002/health")
    gw_ready = wait_for_ready("http://127.0.0.1:8080/health")

    if not (alpha_ready and beta_ready and gw_ready):
        print("ERROR: One or more services failed to start.")
        cleanup()

    print("\n" + "=" * 64)
    print("  All services are live and healthy!")
    print("=" * 64)
    print("  * Ops Console Dashboard: http://localhost:8080/")
    print("  * Provider Alpha (9001): http://127.0.0.1:9001/health")
    print("  * Provider Beta  (9002): http://127.0.0.1:9002/health")
    print("=" * 64)
    print("Press Ctrl+C to stop all servers.\n")

    # Monitor until interrupted
    try:
        while True:
            for p in procs:
                if p.poll() is not None:
                    print(f"Process {p.args} exited unexpectedly with code {p.returncode}")
                    cleanup()
            time.sleep(1)
    except KeyboardInterrupt:
        cleanup()


if __name__ == "__main__":
    main()
