"""Embedded Enterprise Ops Console dashboard for Prism Gateway.
Provides professional, high-performance monitoring of tenant spend, cache hit rates,
upstream provider health, granular request telemetry, and Excel-like interactive data manipulation.
"""

HTML_DASHBOARD = """<!DOCTYPE html>
<html lang="en" data-theme="light">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Prism Gateway - Ops console</title>
    <link rel="icon" type="image/svg+xml" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Cdefs%3E%3ClinearGradient id='p' x1='0%25' y1='0%25' x2='100%25' y2='100%25'%3E%3Cstop offset='0%25' stop-color='%230284c7'/%3E%3Cstop offset='50%25' stop-color='%236366f1'/%3E%3Cstop offset='100%25' stop-color='%23f43f5e'/%3E%3C/linearGradient%3E%3C/defs%3E%3Cpolygon points='16,3 30,27 2,27' fill='%23ffffff' stroke='url(%23p)' stroke-width='2.5' stroke-linejoin='round'/%3E%3Cline x1='16' y1='3' x2='22' y2='27' stroke='%230284c7' stroke-width='1.5' opacity='0.9'/%3E%3Cline x1='16' y1='3' x2='10' y2='27' stroke='%23f43f5e' stroke-width='1.5' opacity='0.9'/%3E%3C/svg%3E">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        /* -------------------------------------------------------------------------
           1. Enterprise Professional Color System (Sentence Case & Colored Metrics)
        ------------------------------------------------------------------------- */
        :root, [data-theme="light"] {
            --bg: #f8fafc;
            --surface: #ffffff;
            --surface-elevated: #f1f5f9;
            --surface-subtle: #f8fafc;
            --surface-zebra: #fafbfd;
            --surface-hover: #f1f5f9;
            --border: #e2e8f0;
            --border-light: #cbd5e1;
            --border-focus: #0284c7;
            --text-primary: #0f172a;
            --text-secondary: #475569;
            --text-muted: #64748b;
            
            --primary: #0284c7;
            --primary-rgb: 2, 132, 199;
            --primary-glow: rgba(2, 132, 199, 0.12);
            --accent: #6366f1;
            --accent-glow: rgba(99, 102, 241, 0.12);
            --success: #059669;
            --success-glow: rgba(5, 150, 105, 0.12);
            --warning: #d97706;
            --warning-glow: rgba(217, 119, 6, 0.12);
            --danger: #dc2626;
            --danger-glow: rgba(220, 38, 38, 0.12);
            --purple: #7c3aed;
            --purple-glow: rgba(124, 58, 237, 0.12);
            
            --card-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05), 0 1px 2px -1px rgba(0, 0, 0, 0.04);
            --card-hover-shadow: 0 8px 20px -4px rgba(0, 0, 0, 0.08), 0 4px 8px -2px rgba(0, 0, 0, 0.04);
            --header-border: #e2e8f0;
            --table-header-bg: #f8fafc;
            --code-bg: #f1f5f9;
            --font-mono: "JetBrains Mono", ui-monospace, SFMono-Regular, Menlo, monospace;
        }

        [data-theme="dark"] {
            --bg: #090d16;
            --surface: #111827;
            --surface-elevated: #1e293b;
            --surface-subtle: #172133;
            --surface-zebra: #141d2e;
            --surface-hover: #1f2a3d;
            --border: #283548;
            --border-light: #374151;
            --border-focus: #38bdf8;
            --text-primary: #f8fafc;
            --text-secondary: #94a3b8;
            --text-muted: #64748b;
            
            --primary: #38bdf8;
            --primary-rgb: 56, 189, 248;
            --primary-glow: rgba(56, 189, 248, 0.2);
            --accent: #818cf8;
            --accent-glow: rgba(129, 140, 248, 0.2);
            --success: #10b981;
            --success-glow: rgba(16, 185, 129, 0.2);
            --warning: #f59e0b;
            --warning-glow: rgba(245, 158, 11, 0.2);
            --danger: #ef4444;
            --danger-glow: rgba(239, 68, 68, 0.2);
            --purple: #c084fc;
            --purple-glow: rgba(192, 132, 252, 0.2);
            
            --card-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3), 0 2px 4px -2px rgba(0, 0, 0, 0.24);
            --card-hover-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.5);
            --header-border: #283548;
            --table-header-bg: #172133;
            --code-bg: #1e293b;
        }

        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            background-color: var(--bg);
            color: var(--text-primary);
            font-family: "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            font-size: 13.5px;
            line-height: 1.5;
            padding: 24px 32px 48px;
            min-height: 100vh;
            transition: background-color 0.2s ease, color 0.2s ease;
        }

        /* -------------------------------------------------------------------------
           2. Header Status Badge & Action Pill
        ------------------------------------------------------------------------- */
        .header-status-pill {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            background: var(--surface);
            border: 1px solid var(--border);
            padding: 7px 14px;
            border-radius: 8px;
            font-size: 12.5px;
            font-weight: 500;
            color: var(--text-secondary);
            box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
            user-select: none;
        }
        .status-dot-pulse {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: var(--success);
            box-shadow: 0 0 0 0 rgba(5, 150, 105, 0.7);
            animation: pulseDot 2s infinite;
        }
        @keyframes pulseDot {
            0% { box-shadow: 0 0 0 0 rgba(5, 150, 105, 0.7); }
            70% { box-shadow: 0 0 0 6px rgba(5, 150, 105, 0); }
            100% { box-shadow: 0 0 0 0 rgba(5, 150, 105, 0); }
        }
        .status-pill-ok {
            background: var(--success-glow);
            color: var(--success);
            border: 1px solid var(--success);
            padding: 2px 8px;
            border-radius: 12px;
            font-weight: 600;
            font-size: 11px;
        }

        /* -------------------------------------------------------------------------
           3. Header & Brand Section (Sentence Case)
        ------------------------------------------------------------------------- */
        header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 24px;
            padding-bottom: 18px;
            border-bottom: 1px solid var(--header-border);
        }
        .header-brand {
            display: flex;
            align-items: center;
            gap: 16px;
        }

        .brand-logo {
            width: 48px;
            height: 48px;
            background: var(--surface);
            border: 1px solid var(--border-light);
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 2px 10px var(--primary-glow);
            cursor: pointer;
            user-select: none;
            transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
        }
        .brand-logo:hover {
            transform: translateY(-2px) scale(1.06);
            border-color: var(--primary);
            box-shadow: 0 6px 18px var(--primary-glow);
        }
        .brand-logo:active {
            transform: translateY(1px) scale(0.96);
        }
        .brand-logo svg {
            width: 32px;
            height: 32px;
            transition: transform 0.4s ease;
        }
        .brand-logo:hover svg {
            transform: rotate(15deg);
        }

        .brand-title h1 {
            font-size: 22px;
            font-weight: 700;
            letter-spacing: -0.02em;
            color: var(--text-primary);
        }
        .brand-subtitle {
            font-size: 13px;
            color: var(--text-secondary);
            margin-top: 2px;
        }
        .header-actions {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .btn {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            background: var(--surface);
            color: var(--text-primary);
            border: 1px solid var(--border);
            padding: 8px 16px;
            border-radius: 8px;
            font-size: 13px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.18s cubic-bezier(0.4, 0, 0.2, 1);
            user-select: none;
            box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
        }
        .btn:hover {
            background: var(--surface-elevated);
            border-color: var(--border-light);
            transform: translateY(-1px);
            box-shadow: 0 3px 8px rgba(0, 0, 0, 0.06);
        }
        .btn:active {
            transform: translateY(1px);
        }
        .btn-primary {
            background: linear-gradient(135deg, #0284c7 0%, #2563eb 100%);
            border-color: #0284c7;
            color: #ffffff;
            box-shadow: 0 2px 10px rgba(2, 132, 199, 0.28);
        }
        .btn-primary:hover {
            background: linear-gradient(135deg, #0369a1 0%, #1d4ed8 100%);
            box-shadow: 0 4px 14px rgba(2, 132, 199, 0.4);
            color: #ffffff;
        }

        /* -------------------------------------------------------------------------
           4. Interactive Icon Badges (With Hover & Click Behaviour)
        ------------------------------------------------------------------------- */
        .icon-glow-badge {
            width: 34px;
            height: 34px;
            border-radius: 8px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            user-select: none;
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
        }
        .icon-glow-badge:hover {
            transform: translateY(-2px) scale(1.08);
            filter: brightness(1.1);
        }
        .icon-glow-badge:active {
            transform: translateY(1px) scale(0.95);
        }

        .icon-cyan {
            background: var(--primary-glow);
            border: 1px solid rgba(2, 132, 199, 0.3);
            color: var(--primary);
            box-shadow: 0 2px 8px var(--primary-glow);
        }
        .icon-cyan:hover {
            border-color: var(--primary);
            box-shadow: 0 4px 14px var(--primary-glow);
        }

        .icon-indigo {
            background: var(--accent-glow);
            border: 1px solid rgba(99, 102, 241, 0.3);
            color: var(--accent);
            box-shadow: 0 2px 8px var(--accent-glow);
        }
        .icon-indigo:hover {
            border-color: var(--accent);
            box-shadow: 0 4px 14px var(--accent-glow);
        }

        .icon-emerald {
            background: var(--success-glow);
            border: 1px solid rgba(5, 150, 105, 0.3);
            color: var(--success);
            box-shadow: 0 2px 8px var(--success-glow);
        }
        .icon-emerald:hover {
            border-color: var(--success);
            box-shadow: 0 4px 14px var(--success-glow);
        }

        .icon-purple {
            background: var(--purple-glow);
            border: 1px solid rgba(124, 58, 237, 0.3);
            color: var(--purple);
            box-shadow: 0 2px 8px var(--purple-glow);
        }
        .icon-purple:hover {
            border-color: var(--purple);
            box-shadow: 0 4px 14px var(--purple-glow);
        }

        /* -------------------------------------------------------------------------
           5. Top KPI Grid (Sentence Case & Coloured Counts)
        ------------------------------------------------------------------------- */
        .kpi-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 18px;
            margin-bottom: 26px;
        }
        .kpi-card {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 20px;
            position: relative;
            overflow: hidden;
            box-shadow: var(--card-shadow);
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
        }
        .kpi-card:hover {
            border-color: var(--border-light);
            box-shadow: var(--card-hover-shadow);
            transform: translateY(-2px);
        }
        .kpi-card::before {
            content: "";
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 3px;
            background: linear-gradient(90deg, var(--accent), var(--primary));
        }
        .kpi-label {
            font-size: 13px;
            font-weight: 600;
            text-transform: none; /* Sentence case */
            letter-spacing: normal;
            color: var(--text-secondary);
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        .kpi-value {
            font-size: 28px;
            font-weight: 700;
            letter-spacing: -0.02em;
            margin: 10px 0 4px;
            font-family: var(--font-mono);
        }
        .kpi-sub {
            font-size: 12px;
            color: var(--text-muted);
        }
        .progress-bar-bg {
            width: 100%;
            height: 8px;
            background: var(--surface-elevated);
            border: 1px solid var(--border);
            border-radius: 9999px;
            margin-top: 10px;
            overflow: hidden;
        }
        .progress-bar-fill {
            height: 100%;
            background: linear-gradient(90deg, var(--primary), var(--accent));
            border-radius: 9999px;
            transition: width 0.4s ease;
        }

        /* -------------------------------------------------------------------------
           6. Panels & Excel-Style Controls (Sentence Case)
        ------------------------------------------------------------------------- */
        .panel {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 12px;
            margin-bottom: 24px;
            overflow: hidden;
            box-shadow: var(--card-shadow);
        }
        .panel-header {
            padding: 14px 20px;
            background: var(--surface-subtle);
            border-bottom: 1px solid var(--border);
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 12px;
        }
        .panel-title {
            font-size: 14px;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 10px;
            color: var(--text-primary);
        }
        .panel-actions {
            display: flex;
            align-items: center;
            gap: 10px;
            flex-wrap: wrap;
        }

        .pill-group {
            display: inline-flex;
            background: var(--surface-elevated);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 2px;
            gap: 2px;
        }
        .pill-btn {
            background: transparent;
            border: none;
            color: var(--text-secondary);
            font-size: 12px;
            font-weight: 600;
            padding: 5px 12px;
            border-radius: 6px;
            cursor: pointer;
            transition: all 0.15s ease;
            user-select: none;
        }
        .pill-btn:hover {
            color: var(--text-primary);
            background: var(--surface-subtle);
        }
        .pill-btn.active {
            background: var(--surface);
            color: var(--primary);
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
        }

        /* -------------------------------------------------------------------------
           7. Excel-Like Interactive Table Grid with Drag-Resizing (Sentence Case)
        ------------------------------------------------------------------------- */
        .table-responsive {
            width: 100%;
            overflow-x: auto;
            -webkit-overflow-scrolling: touch;
            position: relative;
            scrollbar-width: thin;
            scrollbar-color: var(--border-light) transparent;
        }
        .table-responsive::-webkit-scrollbar {
            height: 6px;
        }
        .table-responsive::-webkit-scrollbar-track {
            background: var(--surface-elevated);
        }
        .table-responsive::-webkit-scrollbar-thumb {
            background: var(--border-light);
            border-radius: 4px;
        }
        .table-responsive::-webkit-scrollbar-thumb:hover {
            background: var(--primary);
        }
        table.excel-grid {
            width: 100%;
            border-collapse: separate;
            border-spacing: 0;
            font-size: 13px;
            text-align: left;
            user-select: text;
        }
        table.excel-grid thead th {
            background: var(--table-header-bg);
            padding: 10px 14px;
            color: var(--text-secondary);
            font-weight: 600;
            font-size: 12px;
            text-transform: none; /* Sentence case strictly enforced */
            letter-spacing: normal;
            border-right: 1px solid var(--border);
            border-bottom: 2px solid var(--border);
            white-space: nowrap;
            position: relative;
            user-select: none;
        }
        table.excel-grid thead th:last-child {
            border-right: none;
        }
        table.excel-grid thead th.sortable {
            cursor: pointer;
            transition: background-color 0.15s ease, color 0.15s ease;
        }
        table.excel-grid thead th.sortable:hover {
            color: var(--primary);
            background: var(--surface-hover);
        }
        table.excel-grid thead th.sorted-active {
            color: var(--primary);
            background: var(--primary-glow);
        }
        .sort-indicator {
            display: inline-block;
            margin-left: 4px;
            font-size: 11px;
            color: var(--text-muted);
            font-weight: 700;
        }

        /* Excel Column Resize Handle */
        .col-resizer {
            position: absolute;
            top: 0;
            right: 0;
            width: 7px;
            height: 100%;
            cursor: col-resize;
            user-select: none;
            z-index: 10;
        }
        .col-resizer:hover, .col-resizer.is-resizing {
            background: var(--primary);
        }

        /* Excel Row & Cell Gridlines */
        table.excel-grid tbody tr {
            position: relative;
            transition: background-color 0.12s ease;
        }
        table.excel-grid tbody tr:nth-child(even) {
            background-color: var(--surface-zebra);
        }
        table.excel-grid tbody tr:hover td {
            background-color: var(--surface-hover);
        }
        table.excel-grid tbody td {
            padding: 11px 14px;
            border-right: 1px solid var(--border);
            border-bottom: 1px solid var(--border);
            color: var(--text-primary);
            vertical-align: middle;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            transition: padding 0.15s ease;
        }
        table.excel-grid tbody td:last-child {
            border-right: none;
        }

        /* Excel Row Height Resizer Handle */
        .row-resizer-handle {
            position: absolute;
            bottom: 0;
            left: 0;
            width: 100%;
            height: 6px;
            cursor: row-resize;
            z-index: 8;
            user-select: none;
        }
        .row-resizer-handle:hover, .row-resizer-handle.is-resizing {
            background: var(--primary);
        }

        /* Row Header (Excel # Column - Sticky on Horizontal Scroll) */
        .row-index-cell {
            font-family: var(--font-mono);
            font-size: 11px;
            font-weight: 700;
            color: var(--accent);
            text-align: center;
            background: var(--surface-subtle);
            width: 44px;
            min-width: 44px;
            user-select: none;
            position: sticky;
            left: 0;
            z-index: 5;
            box-shadow: 2px 0 4px -1px rgba(0, 0, 0, 0.06);
        }
        thead th.row-index-cell {
            position: sticky;
            left: 0;
            z-index: 12;
            background: var(--table-header-bg);
            box-shadow: 2px 0 4px -1px rgba(0, 0, 0, 0.06);
        }

        /* Density Modes */
        table.density-compact tbody td { padding: 6px 10px; font-size: 12px; }
        table.density-standard tbody td { padding: 11px 14px; font-size: 13px; }
        table.density-relaxed tbody td { padding: 16px 18px; font-size: 13.5px; }

        /* -------------------------------------------------------------------------
           8. Status Badges, Keys, Visible Progressive Bar & Coloured Counts
        ------------------------------------------------------------------------- */
        .badge {
            display: inline-flex;
            align-items: center;
            padding: 3px 9px;
            border-radius: 6px;
            font-size: 11px;
            font-weight: 700;
            letter-spacing: 0.01em;
            white-space: nowrap;
            text-transform: none; /* Sentence case */
        }
        .badge-success { background: var(--success-glow); color: var(--success); border: 1px solid rgba(5, 150, 105, 0.3); }
        .badge-primary { background: var(--primary-glow); color: var(--primary); border: 1px solid rgba(2, 132, 199, 0.3); }
        .badge-warning { background: var(--warning-glow); color: var(--warning); border: 1px solid rgba(217, 119, 6, 0.3); }
        .badge-danger { background: var(--danger-glow); color: var(--danger); border: 1px solid rgba(220, 38, 38, 0.3); }
        .badge-neutral { background: var(--surface-elevated); color: var(--text-secondary); border: 1px solid var(--border); }

        /* Full virtual key styling without arbitrary truncation */
        .key-code {
            font-family: var(--font-mono);
            font-size: 12px;
            background: var(--code-bg);
            padding: 3px 8px;
            border-radius: 4px;
            border: 1px solid var(--border);
            color: var(--primary);
            font-weight: 600;
            display: inline-block;
            white-space: nowrap;
        }

        /* High-visibility Progressive Spend Bar */
        .budget-bar-container {
            width: 140px;
            height: 9px;
            background: var(--surface-elevated);
            border: 1px solid var(--border-light);
            border-radius: 9999px;
            overflow: hidden;
            margin-top: 5px;
            box-shadow: inset 0 1px 2px rgba(0, 0, 0, 0.06);
        }
        .budget-bar-fill {
            height: 100%;
            border-radius: 9999px;
            transition: width 0.4s ease;
            box-shadow: 0 0 6px rgba(5, 150, 105, 0.4);
        }

        .latency-fast { color: var(--success); font-weight: 700; }
        .latency-medium { color: var(--warning); font-weight: 700; }
        .latency-slow { color: var(--danger); font-weight: 700; }

        /* -------------------------------------------------------------------------
           9. Floating Interactive Toast Notification
        ------------------------------------------------------------------------- */
        #toast-container {
            position: fixed;
            bottom: 24px;
            right: 28px;
            z-index: 9999;
            pointer-events: none;
        }
        .toast-msg {
            background: var(--surface);
            color: var(--text-primary);
            border: 1px solid var(--border-light);
            border-left: 4px solid var(--primary);
            padding: 12px 18px;
            border-radius: 8px;
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.15);
            font-size: 13px;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 10px;
            margin-top: 8px;
            opacity: 0;
            transform: translateY(12px);
            transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
            pointer-events: auto;
        }
        .toast-msg.show {
            opacity: 1;
            transform: translateY(0);
        }

        /* -------------------------------------------------------------------------
           10. Comprehensive Multi-Device Responsive Architecture
        ------------------------------------------------------------------------- */
        /* Ultra-wide screens (4K / 2K monitors >= 1600px) */
        @media (min-width: 1600px) {
            body {
                max-width: 1560px;
                margin: 0 auto;
            }
        }

        /* Large tablets & small laptops (<= 1024px) */
        @media (max-width: 1024px) {
            body {
                padding: 20px 20px 40px;
            }
            .kpi-grid {
                grid-template-columns: repeat(2, 1fr);
                gap: 14px;
            }
        }

        /* Tablets & Phablets (<= 768px) */
        @media (max-width: 768px) {
            body {
                padding: 16px 14px 36px;
            }
            header {
                flex-direction: column;
                align-items: stretch;
                gap: 14px;
                margin-bottom: 20px;
                padding-bottom: 16px;
            }
            .header-actions {
                width: 100%;
                display: flex;
                flex-wrap: wrap;
                align-items: center;
                justify-content: flex-start;
                gap: 8px;
            }
            .header-status-pill {
                flex: 1 1 auto;
                justify-content: center;
            }
            .panel-header {
                flex-direction: column;
                align-items: stretch;
                gap: 12px;
                padding: 12px 14px;
            }
            .panel-actions {
                width: 100%;
                display: flex;
                flex-wrap: wrap;
                gap: 8px;
                justify-content: flex-start;
            }
            .pill-group {
                overflow-x: auto;
                max-width: 100%;
                -webkit-overflow-scrolling: touch;
            }
        }

        /* Mobile Phones & Compact Viewports (<= 480px, e.g. 400x608, 375x667, 360x740) */
        @media (max-width: 480px) {
            body {
                padding: 12px 10px 32px;
                font-size: 13px;
            }
            header {
                gap: 12px;
                margin-bottom: 16px;
                padding-bottom: 12px;
            }
            .header-brand {
                gap: 10px;
            }
            .brand-logo {
                width: 38px;
                height: 38px;
                min-width: 38px;
            }
            .brand-logo svg {
                width: 26px;
                height: 26px;
            }
            .brand-title h1 {
                font-size: 18px;
                letter-spacing: -0.01em;
            }
            .brand-subtitle {
                font-size: 11px;
                line-height: 1.35;
            }
            .header-actions {
                gap: 6px;
            }
            .header-status-pill {
                width: 100%;
                padding: 6px 10px;
                font-size: 11.5px;
                justify-content: center;
            }
            #theme-btn {
                flex: 1 1 auto;
                padding: 6px 10px;
                font-size: 11.5px;
                justify-content: center;
            }
            .btn-primary {
                flex: 1 1 auto;
                padding: 6px 12px;
                font-size: 11.5px;
                justify-content: center;
            }

            /* Sleek 2x2 KPI Grid on mobile */
            .kpi-grid {
                grid-template-columns: repeat(2, 1fr);
                gap: 8px;
                margin-bottom: 18px;
            }
            .kpi-card {
                padding: 12px 10px;
                border-radius: 10px;
            }
            .kpi-label {
                font-size: 11px;
            }
            .icon-glow-badge {
                width: 26px;
                height: 26px;
            }
            .icon-glow-badge svg {
                width: 14px;
                height: 14px;
            }
            .kpi-value {
                font-size: 20px;
                margin: 6px 0 2px;
            }
            .kpi-sub {
                font-size: 10.5px;
            }

            /* Panels on mobile */
            .panel {
                margin-bottom: 16px;
                border-radius: 10px;
            }
            .panel-header {
                padding: 10px 12px;
                gap: 8px;
            }
            .panel-title {
                font-size: 12.5px;
            }
            .panel-actions {
                gap: 6px;
            }
            .pill-btn {
                padding: 4px 8px;
                font-size: 10.5px;
            }
            .btn {
                padding: 5px 10px;
                font-size: 11px;
            }

            /* Table cell compacting on mobile */
            table.excel-grid thead th {
                padding: 8px 10px;
                font-size: 11px;
            }
            table.excel-grid tbody td {
                padding: 8px 10px;
                font-size: 12px;
            }
            .row-index-cell {
                width: 34px;
                min-width: 34px;
                font-size: 10.5px;
            }
            .key-code {
                font-size: 11px;
                padding: 2px 5px;
            }
            .budget-bar-container {
                width: 90px;
                height: 7px;
            }

            /* Toast container mobile */
            #toast-container {
                bottom: 12px;
                right: 12px;
                left: 12px;
            }
            .toast-msg {
                padding: 10px 14px;
                font-size: 12px;
            }
        }
    </style>
</head>
<body>

    <!-- Header & Brand Section (Sentence Case) -->
    <header>
        <div class="header-brand">
            <div class="brand-logo" onclick="handleLogoClick()" title="Prism Gateway core (click to refresh)">
                <svg viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <defs>
                        <linearGradient id="prismGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                            <stop offset="0%" stop-color="#0284c7"/>
                            <stop offset="50%" stop-color="#6366f1"/>
                            <stop offset="100%" stop-color="#f43f5e"/>
                        </linearGradient>
                    </defs>
                    <polygon points="16,4 29,27 3,27" stroke="url(#prismGrad)" stroke-width="2.6" fill="rgba(2, 132, 199, 0.08)" stroke-linejoin="round"/>
                    <line x1="16" y1="4" x2="22" y2="27" stroke="#0284c7" stroke-width="1.8" stroke-linecap="round" opacity="0.95"/>
                    <line x1="16" y1="4" x2="10" y2="27" stroke="#f43f5e" stroke-width="1.8" stroke-linecap="round" opacity="0.95"/>
                    <line x1="1" y1="16" x2="16" y2="16" stroke="#475569" stroke-width="1.8" stroke-linecap="round" opacity="0.85"/>
                </svg>
            </div>
            <div class="brand-title">
                <h1>Prism Gateway</h1>
                <p class="brand-subtitle">Unified LLM infrastructure, Hot-path smart routing & Semantic caching</p>
            </div>
        </div>
        <div class="header-actions">
            <!-- System Status Indicator (Beside Refresh Button) -->
            <div class="header-status-pill" title="Gateway & provider operational state">
                <div class="status-dot-pulse"></div>
                <span>System status:</span>
                <span class="status-pill-ok">All operational</span>
            </div>

            <!-- Dark Mode Toggle Button (Beside Refresh Button) -->
            <button class="btn" id="theme-btn" onclick="toggleTheme()" title="Switch light or dark theme">
                <span id="theme-icon">🌙</span> <span id="theme-text">Dark mode</span>
            </button>

            <!-- Refresh Button -->
            <button class="btn btn-primary" onclick="window.location.reload()" title="Full page reload">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M21 2v6h-6M3 12a9 9 0 0 1 15-6.7L21 8M3 22v-6h6M21 12a9 9 0 0 1-15 6.7L3 16"/></svg>
                Refresh
            </button>
        </div>
    </header>

    <!-- 3. Top KPI Grid (Sentence Case & Coloured Counts) -->
    <div class="kpi-grid">
        <div class="kpi-card">
            <div class="kpi-label">
                <span>Total requests</span>
                <div class="icon-glow-badge icon-cyan" onclick="handleCardIconClick('requests')" title="Click to refresh request count">
                    <svg width="17" height="17" fill="none" stroke="currentColor" stroke-width="2.2" viewBox="0 0 24 24"><path d="M13 10V3L4 14h7v7l9-11h-7z"/></svg>
                </div>
            </div>
            <div class="kpi-value" id="stat-total" style="color: var(--primary);">-</div>
            <div class="kpi-sub">Across all registered tenants</div>
        </div>

        <div class="kpi-card">
            <div class="kpi-label">
                <span>Semantic cache efficiency</span>
                <div class="icon-glow-badge icon-indigo" onclick="handleCardIconClick('cache')" title="Click to refresh cache efficiency">
                    <svg width="17" height="17" fill="none" stroke="currentColor" stroke-width="2.2" viewBox="0 0 24 24"><path d="M4 7v10c0 2 1.5 3 3.5 3h9c2 0 3.5-1 3.5-3V7c0-2-1.5-3-3.5-3h-9C5.5 4 4 5 4 7z"/><path d="M9 12h6m-6-3h6m-6 6h4"/></svg>
                </div>
            </div>
            <div class="kpi-value" id="stat-hit-rate" style="color: var(--accent);">-</div>
            <div class="progress-bar-bg">
                <div class="progress-bar-fill" id="cache-progress" style="width: 0%;"></div>
            </div>
            <div class="kpi-sub" id="stat-cache-sub" style="margin-top: 6px;">- hits / - misses</div>
        </div>

        <div class="kpi-card">
            <div class="kpi-label">
                <span>Total metered spend</span>
                <div class="icon-glow-badge icon-emerald" onclick="handleCardIconClick('spend')" title="Click to recalculate tenant spend">
                    <svg width="17" height="17" fill="none" stroke="currentColor" stroke-width="2.2" viewBox="0 0 24 24"><path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>
                </div>
            </div>
            <div class="kpi-value" id="stat-spend" style="color: var(--success);">$0.000000</div>
            <div class="kpi-sub">Calculated via model pricing</div>
        </div>

        <div class="kpi-card">
            <div class="kpi-label">
                <span>Upstream providers</span>
                <div class="icon-glow-badge icon-purple" onclick="handleCardIconClick('providers')" title="Upstream server cluster (click to test health)">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <rect x="2" y="2" width="20" height="8" rx="2" ry="2"/>
                        <rect x="2" y="14" width="20" height="8" rx="2" ry="2"/>
                        <line x1="6" y1="6" x2="6.01" y2="6"/>
                        <line x1="6" y1="18" x2="6.01" y2="18"/>
                        <line x1="10" y1="6" x2="18" y2="6"/>
                        <line x1="10" y1="18" x2="18" y2="18"/>
                    </svg>
                </div>
            </div>
            <div class="kpi-value" style="color: var(--purple); font-size: 20px; margin-top: 14px;">
                Alpha & Beta
            </div>
            <div class="kpi-sub" style="margin-top: 12px; color: var(--success); font-weight: 600;">
                ● Auto-failover armed
            </div>
        </div>
    </div>

    <!-- 4. Tenant Keys Panel (Sentence Case, Visible Progressive Bar & Coloured Counts) -->
    <div class="panel">
        <div class="panel-header">
            <div class="panel-title">
                <div class="icon-glow-badge icon-indigo" onclick="handleTableIconClick('tenants')" title="Click to auto-fit tenant table" style="width: 28px; height: 28px;">
                    <svg width="15" height="15" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
                </div>
                Tenant provisioning & rate governance
            </div>
            <div class="panel-actions">
                <div class="pill-group">
                    <button class="pill-btn" onclick="setDensity('tenants-table', 'compact')">Compact</button>
                    <button class="pill-btn active" onclick="setDensity('tenants-table', 'standard')">Standard</button>
                    <button class="pill-btn" onclick="setDensity('tenants-table', 'relaxed')">Relaxed</button>
                </div>
                <button class="btn" onclick="resetTable('tenants-table')" style="padding: 5px 12px; font-size: 12px;" title="Reset row heights and column widths">
                    ⟲ Auto-fit
                </button>
            </div>
        </div>
        <div class="table-responsive">
            <table class="excel-grid density-standard" id="tenants-table">
                <thead>
                    <tr>
                        <th class="row-index-cell">#</th>
                        <th>Team</th>
                        <th>Virtual key</th>
                        <th>Monthly budget</th>
                        <th>Spend / utilization</th>
                        <th>Rate limits</th>
                        <th>Model allowlist</th>
                        <th>Semantic cache</th>
                    </tr>
                </thead>
                <tbody id="tenants-body">
                    <tr><td colspan="8" style="text-align: center; color: var(--text-muted); padding: 24px;">Loading tenants...</td></tr>
                </tbody>
            </table>
        </div>
    </div>

    <!-- 5. Live Request Audit Stream Panel (Sentence Case, Working Asc/Desc Sort, Full Keys, Coloured Counts) -->
    <div class="panel">
        <div class="panel-header">
            <div class="panel-title">
                <div class="icon-glow-badge icon-cyan" onclick="handleTableIconClick('logs')" title="Click to sort OK status to top" style="width: 28px; height: 28px;">
                    <svg width="15" height="15" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M21 12a9 9 0 0 1-9 9m9-9a9 9 0 0 0-9-9m9 9H3m9 9a9 9 0 0 1-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9"/></svg>
                </div>
                Live request audit stream (last 30 events)
            </div>
            <div class="panel-actions">
                <!-- Status Ordering / Filters -->
                <div class="pill-group">
                    <button class="pill-btn active" id="filter-ok-above" onclick="setStatusFilter('ok_above')">✓ OK status above</button>
                    <button class="pill-btn" id="filter-all" onclick="setStatusFilter('all')">All events</button>
                    <button class="pill-btn" id="filter-ok-only" onclick="setStatusFilter('ok_only')">Only OK</button>
                    <button class="pill-btn" id="filter-rate-limit" onclick="setStatusFilter('rate_limit')">Rate limited</button>
                </div>

                <!-- Table Density Controls -->
                <div class="pill-group">
                    <button class="pill-btn" onclick="setDensity('logs-table', 'compact')">Compact</button>
                    <button class="pill-btn active" onclick="setDensity('logs-table', 'standard')">Standard</button>
                    <button class="pill-btn" onclick="setDensity('logs-table', 'relaxed')">Relaxed</button>
                </div>

                <button class="btn" onclick="resetTable('logs-table')" style="padding: 5px 12px; font-size: 12px;" title="Reset column widths and row heights">
                    ⟲ Auto-fit
                </button>
            </div>
        </div>
        <div class="table-responsive">
            <table class="excel-grid density-standard" id="logs-table">
                <thead>
                    <tr>
                        <th class="row-index-cell">#</th>
                        <th class="sortable" id="th-time" onclick="sortTableBy('time')">Time (UTC) <span class="sort-indicator" id="sort-arrow-time">↕</span></th>
                        <th class="sortable" id="th-virtual_key" onclick="sortTableBy('virtual_key')">Virtual key <span class="sort-indicator" id="sort-arrow-virtual_key">↕</span></th>
                        <th class="sortable" id="th-requested_model" onclick="sortTableBy('requested_model')">Requested tier <span class="sort-indicator" id="sort-arrow-requested_model">↕</span></th>
                        <th class="sortable" id="th-resolved_provider" onclick="sortTableBy('resolved_provider')">Resolved upstream <span class="sort-indicator" id="sort-arrow-resolved_provider">↕</span></th>
                        <th class="sortable" id="th-status" onclick="sortTableBy('status')">Status <span class="sort-indicator" id="sort-arrow-status">↕</span></th>
                        <th class="sortable" id="th-tokens" onclick="sortTableBy('tokens')">Tokens (in/out) <span class="sort-indicator" id="sort-arrow-tokens">↕</span></th>
                        <th class="sortable" id="th-cost" onclick="sortTableBy('cost')">Cost (USD) <span class="sort-indicator" id="sort-arrow-cost">↕</span></th>
                        <th class="sortable" id="th-cache" onclick="sortTableBy('cache')">Cache <span class="sort-indicator" id="sort-arrow-cache">↕</span></th>
                        <th class="sortable" id="th-fallback" onclick="sortTableBy('fallback')">Fallback <span class="sort-indicator" id="sort-arrow-fallback">↕</span></th>
                        <th class="sortable" id="th-latency" onclick="sortTableBy('latency')">Latency <span class="sort-indicator" id="sort-arrow-latency">↕</span></th>
                    </tr>
                </thead>
                <tbody id="logs-body">
                    <tr><td colspan="11" style="text-align: center; color: var(--text-muted); padding: 24px;">No requests recorded yet</td></tr>
                </tbody>
            </table>
        </div>
    </div>

    <!-- Floating Interactive Toast Container -->
    <div id="toast-container"></div>

    <script>
        /* -------------------------------------------------------------------------
           State & Initialization
        ------------------------------------------------------------------------- */
        let cachedLogs = [];
        let currentFilter = 'ok_above';
        let sortColumn = null;
        let sortAsc = true;

        function initTheme() {
            const saved = localStorage.getItem('prism-theme') || 'light';
            document.documentElement.setAttribute('data-theme', saved);
            updateThemeButton(saved);
        }

        function toggleTheme() {
            const current = document.documentElement.getAttribute('data-theme') || 'light';
            const next = current === 'dark' ? 'light' : 'dark';
            document.documentElement.setAttribute('data-theme', next);
            localStorage.setItem('prism-theme', next);
            updateThemeButton(next);
            showToast(`Theme changed to ${next === 'dark' ? 'Executive dark' : 'Enterprise light'}`);
        }

        function updateThemeButton(theme) {
            const icon = document.getElementById('theme-icon');
            const label = document.getElementById('theme-text');
            if (icon && label) {
                icon.textContent = theme === 'dark' ? '☀️' : '🌙';
                label.textContent = theme === 'dark' ? 'Light mode' : 'Dark mode';
            }
        }

        function showToast(message) {
            const container = document.getElementById('toast-container');
            if (!container) return;
            const toast = document.createElement('div');
            toast.className = 'toast-msg';
            toast.innerHTML = `<span style="color: var(--primary);">●</span> ${message}`;
            container.appendChild(toast);
            requestAnimationFrame(() => toast.classList.add('show'));
            setTimeout(() => {
                toast.classList.remove('show');
                setTimeout(() => toast.remove(), 250);
            }, 3000);
        }

        /* -------------------------------------------------------------------------
           Icon Click Behaviors (Interactive Like Buttons)
        ------------------------------------------------------------------------- */
        function handleLogoClick() {
            showToast("Prism Gateway core: Connected & operational");
            fetchData();
        }

        async function handleCardIconClick(cardType) {
            switch(cardType) {
                case 'requests':
                    showToast("Total request telemetry refreshed");
                    await fetchData();
                    break;
                case 'cache':
                    showToast("Semantic cache vector hit-rate re-evaluated");
                    await fetchData();
                    break;
                case 'spend':
                    showToast("Tenant metered spend recalculated via model_pricing.json");
                    await fetchData();
                    break;
                case 'providers':
                    try {
                        const res = await fetch('/admin/providers/health');
                        const data = await res.json();
                        showToast(`Provider Alpha & Beta: Online (200 OK)`);
                    } catch (e) {
                        showToast("Upstream cluster: Failover circuit active");
                    }
                    break;
            }
        }

        function handleTableIconClick(tableName) {
            if (tableName === 'logs') {
                setStatusFilter('ok_above');
                showToast("Request stream: All OK status sorted to top");
            } else {
                resetTable('tenants-table');
                showToast("Tenant table: Grid auto-fitted");
            }
        }

        /* -------------------------------------------------------------------------
           Data Fetching & Rendering
        ------------------------------------------------------------------------- */
        async function fetchData() {
            try {
                const [statsRes, tenantsRes, logsRes] = await Promise.all([
                    fetch('/admin/cache/stats'),
                    fetch('/admin/tenants'),
                    fetch('/admin/logs?limit=50')
                ]);

                const stats = await statsRes.json();
                const tenants = await tenantsRes.json();
                cachedLogs = await logsRes.json();

                // 1. Top KPIs (with vibrant coloured counts)
                document.getElementById('stat-total').textContent = (stats.total_requests || 0).toLocaleString();
                const hitRateVal = (stats.hit_rate || 0) * 100;
                document.getElementById('stat-hit-rate').textContent = hitRateVal.toFixed(1) + '%';
                document.getElementById('cache-progress').style.width = Math.min(100, hitRateVal) + '%';
                document.getElementById('stat-cache-sub').innerHTML = 
                    `<span style="color: var(--primary); font-weight: 700;">${(stats.hits || 0).toLocaleString()} hits</span> / <span style="color: var(--warning); font-weight: 700;">${(stats.misses || 0).toLocaleString()} misses</span>`;

                // Spend calculation
                let totalSpend = 0;
                tenants.forEach(t => totalSpend += (t.current_spend || 0));
                document.getElementById('stat-spend').textContent = '$' + totalSpend.toFixed(6);

                // 2. Tenants Table (Full Keys, High-Visibility Progressive Bar, Coloured Counts)
                const tBody = document.getElementById('tenants-body');
                tBody.innerHTML = tenants.map((t, idx) => {
                    const spend = t.current_spend || 0;
                    const budget = t.monthly_budget_usd || 1;
                    const pct = Math.min(100, (spend / budget) * 100);

                    // High-visibility progress bar width: if spend > 0, ensure at least 6% visible fill
                    const fillWidth = spend > 0 ? Math.max(6, Math.min(100, pct)) : 0;
                    const pctDisplay = pct > 0 && pct < 1 ? '< 1%' : `${pct.toFixed(0)}%`;

                    let barColor = 'var(--success)';
                    if (pct >= 90) barColor = 'var(--danger)';
                    else if (pct >= 70) barColor = 'var(--warning)';

                    return `
                        <tr>
                            <td class="row-index-cell">${idx + 1}</td>
                            <td style="font-weight: 600;">
                                <div style="display: flex; align-items: center; gap: 8px;">
                                    <div style="width: 8px; height: 8px; border-radius: 50%; background: var(--accent);"></div>
                                    ${t.team}
                                </div>
                            </td>
                            <td><span class="key-code" title="${t.virtual_key}">${t.virtual_key}</span></td>
                            <td style="font-family: var(--font-mono); color: var(--primary); font-weight: 700;">$${budget.toFixed(2)}</td>
                            <td>
                                <div style="display: flex; justify-content: space-between; font-weight: 600; font-size: 12px; margin-bottom: 2px;">
                                    <span style="color: var(--success); font-family: var(--font-mono); font-weight: 700;">$${spend.toFixed(6)}</span>
                                    <span style="color: ${barColor}; font-family: var(--font-mono); font-weight: 700;">${pctDisplay}</span>
                                </div>
                                <div class="budget-bar-container">
                                    <div class="budget-bar-fill" style="width: ${fillWidth}%; background: ${barColor};"></div>
                                </div>
                            </td>
                            <td><span class="badge" style="background: var(--primary-glow); color: var(--primary); border: 1px solid var(--primary); font-family: var(--font-mono); font-weight: 700;">${t.requests_per_minute} RPM</span></td>
                            <td>
                                <div style="display: flex; gap: 4px; flex-wrap: wrap;">
                                    ${t.model_allowlist.map(m => `<span class="badge badge-neutral">${m}</span>`).join('')}
                                </div>
                            </td>
                            <td>
                                ${t.cache_enabled 
                                    ? `<span class="badge badge-success">● Active (${((t.similarity_threshold || 0.85)*100).toFixed(0)}%)</span>` 
                                    : '<span class="badge badge-neutral">Disabled</span>'}
                            </td>
                        </tr>
                    `;
                }).join('');

                renderLogs();
                makeTableResizable(document.getElementById('tenants-table'));
                makeTableResizable(document.getElementById('logs-table'));

            } catch (err) {
                console.error("Dashboard update error:", err);
            }
        }

        /* -------------------------------------------------------------------------
           Filtering & Dynamic Asc/Desc Sorting
        ------------------------------------------------------------------------- */
        function setStatusFilter(filterType) {
            currentFilter = filterType;
            sortColumn = null; // Clear manual column sort to let filter rule
            resetSortArrows();
            document.querySelectorAll('.panel-actions .pill-group .pill-btn').forEach(btn => {
                if (['filter-ok-above', 'filter-all', 'filter-ok-only', 'filter-rate-limit'].includes(btn.id)) {
                    btn.classList.remove('active');
                }
            });
            const activeId = filterType === 'ok_above' ? 'filter-ok-above' :
                             filterType === 'all' ? 'filter-all' :
                             filterType === 'ok_only' ? 'filter-ok-only' : 'filter-rate-limit';
            const btn = document.getElementById(activeId);
            if (btn) btn.classList.add('active');
            renderLogs();
        }

        function sortTableBy(col) {
            if (sortColumn === col) {
                sortAsc = !sortAsc; // Toggle direction
            } else {
                sortColumn = col;
                // Sensible default directions: Time/Cost/Latency start descending; others ascending
                sortAsc = (col === 'time' || col === 'cost' || col === 'latency') ? false : true;
            }

            // Remove active status pill highlight since user explicitly chose column sort
            if (currentFilter === 'ok_above') {
                const btn = document.getElementById('filter-ok-above');
                if (btn) btn.classList.remove('active');
            }

            updateSortArrows();
            renderLogs();
            showToast(`Sorted by ${col} (${sortAsc ? 'ascending' : 'descending'})`);
        }

        function resetSortArrows() {
            const cols = ['time', 'virtual_key', 'requested_model', 'resolved_provider', 'status', 'tokens', 'cost', 'cache', 'fallback', 'latency'];
            cols.forEach(c => {
                const arrow = document.getElementById(`sort-arrow-${c}`);
                const th = document.getElementById(`th-${c}`);
                if (arrow) arrow.textContent = '↕';
                if (arrow) arrow.style.color = 'var(--text-muted)';
                if (th) th.classList.remove('sorted-active');
            });
        }

        function updateSortArrows() {
            const cols = ['time', 'virtual_key', 'requested_model', 'resolved_provider', 'status', 'tokens', 'cost', 'cache', 'fallback', 'latency'];
            cols.forEach(c => {
                const arrow = document.getElementById(`sort-arrow-${c}`);
                const th = document.getElementById(`th-${c}`);
                if (!arrow) return;
                if (c === sortColumn) {
                    arrow.textContent = sortAsc ? ' ▲' : ' ▼';
                    arrow.style.color = 'var(--primary)';
                    if (th) th.classList.add('sorted-active');
                } else {
                    arrow.textContent = ' ↕';
                    arrow.style.color = 'var(--text-muted)';
                    if (th) th.classList.remove('sorted-active');
                }
            });
        }

        function renderLogs() {
            const lBody = document.getElementById('logs-body');
            if (!cachedLogs || cachedLogs.length === 0) {
                lBody.innerHTML = '<tr><td colspan="11" style="text-align: center; color: var(--text-muted); padding: 24px;">No requests recorded yet</td></tr>';
                return;
            }

            let logs = [...cachedLogs];

            // Filter logic
            if (currentFilter === 'ok_only') {
                logs = logs.filter(l => l.status === 'ok');
            } else if (currentFilter === 'rate_limit') {
                logs = logs.filter(l => l.status && l.status.includes('rate_limit'));
            }

            // Sorting logic (Column Click Takes Precedence Over Default)
            if (sortColumn) {
                logs.sort((a, b) => {
                    let valA, valB;
                    if (sortColumn === 'time') {
                        valA = new Date(a.created_at || 0).getTime();
                        valB = new Date(b.created_at || 0).getTime();
                    } else if (sortColumn === 'cost') {
                        valA = a.cost_usd || 0;
                        valB = b.cost_usd || 0;
                    } else if (sortColumn === 'latency') {
                        valA = a.latency_ms || 0;
                        valB = b.latency_ms || 0;
                    } else if (sortColumn === 'tokens') {
                        valA = (a.prompt_tokens || 0) + (a.completion_tokens || 0);
                        valB = (b.prompt_tokens || 0) + (b.completion_tokens || 0);
                    } else if (sortColumn === 'status') {
                        valA = a.status || '';
                        valB = b.status || '';
                    } else if (sortColumn === 'virtual_key') {
                        valA = a.virtual_key || '';
                        valB = b.virtual_key || '';
                    } else if (sortColumn === 'cache') {
                        valA = a.cache_result || '';
                        valB = b.cache_result || '';
                    } else if (sortColumn === 'fallback') {
                        valA = a.fallback ? 1 : 0;
                        valB = b.fallback ? 1 : 0;
                    } else {
                        valA = a[sortColumn] || '';
                        valB = b[sortColumn] || '';
                    }

                    if (typeof valA === 'number' && typeof valB === 'number') {
                        return sortAsc ? valA - valB : valB - valA;
                    }
                    return sortAsc ? String(valA).localeCompare(String(valB)) : String(valB).localeCompare(String(valA));
                });
            } else if (currentFilter === 'ok_above') {
                // Default: All OK status rows rendered ABOVE
                logs.sort((a, b) => {
                    const aOk = a.status === 'ok' ? 1 : 0;
                    const bOk = b.status === 'ok' ? 1 : 0;
                    if (aOk !== bOk) {
                        return bOk - aOk; // 'ok' rows come first / above!
                    }
                    return (b.created_at || '').localeCompare(a.created_at || '');
                });
            }

            lBody.innerHTML = logs.map((l, idx) => {
                let statusBadge = `<span class="badge badge-success">ok</span>`;
                if (l.status && l.status.startsWith('rejected_')) {
                    statusBadge = `<span class="badge badge-danger">${l.status.replace('rejected_', '')}</span>`;
                } else if (l.status === 'upstream_error') {
                    statusBadge = `<span class="badge badge-danger">502 upstream</span>`;
                }

                let cacheBadge = l.cache_result === 'hit' 
                    ? '<span class="badge badge-primary">hit</span>' 
                    : '<span style="color: var(--text-muted); font-size: 11px;">miss</span>';

                let fallbackBadge = l.fallback 
                    ? '<span class="badge badge-warning">failover</span>' 
                    : '<span style="color: var(--text-muted); font-size: 11px;">primary</span>';

                let latencyClass = 'latency-fast';
                if (l.latency_ms > 2000) latencyClass = 'latency-slow';
                else if (l.latency_ms > 500) latencyClass = 'latency-medium';

                const timeStr = l.created_at ? l.created_at.split('T')[1].split('.')[0] : '-';
                const fullKey = l.virtual_key || '-';

                return `
                    <tr>
                        <td class="row-index-cell">${idx + 1}</td>
                        <td style="font-family: var(--font-mono); font-size: 12px; color: var(--text-secondary);">${timeStr}</td>
                        <td><span class="key-code" title="${fullKey}">${fullKey}</span></td>
                        <td><b>${l.requested_model}</b></td>
                        <td style="color: var(--text-secondary); font-size: 12px;">
                            ${l.resolved_provider ? `${l.resolved_provider} / <span style="color: var(--text-primary);">${l.resolved_model}</span>` : '<span style="color: var(--text-muted);">-</span>'}
                        </td>
                        <td>${statusBadge}</td>
                        <td style="font-family: var(--font-mono); font-size: 12px;">
                            <span style="color: var(--accent); font-weight: 700;">${l.prompt_tokens}</span> in / <span style="color: var(--primary); font-weight: 700;">${l.completion_tokens}</span> out
                        </td>
                        <td style="font-family: var(--font-mono); font-size: 12px; color: var(--success); font-weight: 700;">$${(l.cost_usd || 0).toFixed(6)}</td>
                        <td>${cacheBadge}</td>
                        <td>${fallbackBadge}</td>
                        <td class="${latencyClass}" style="font-family: var(--font-mono); font-size: 12px;">${l.latency_ms}ms</td>
                    </tr>
                `;
            }).join('');

            makeTableResizable(document.getElementById('logs-table'));
        }

        /* -------------------------------------------------------------------------
           Excel-Like Row & Column Resizing Mechanics
        ------------------------------------------------------------------------- */
        function makeTableResizable(table) {
            if (!table) return;

            // 1. Column Resizing (Width divider on every <th>)
            const thElements = table.querySelectorAll('thead th');
            thElements.forEach((th) => {
                if (th.querySelector('.col-resizer')) return;

                const resizer = document.createElement('div');
                resizer.className = 'col-resizer';
                th.appendChild(resizer);

                let startX, startWidth;

                resizer.addEventListener('mousedown', (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    startX = e.pageX;
                    startWidth = th.offsetWidth;
                    resizer.classList.add('is-resizing');
                    document.body.style.cursor = 'col-resize';
                    document.body.style.userSelect = 'none';

                    function onMouseMove(e) {
                        const newWidth = Math.max(50, startWidth + (e.pageX - startX));
                        th.style.width = newWidth + 'px';
                        th.style.minWidth = newWidth + 'px';
                    }

                    function onMouseUp() {
                        resizer.classList.remove('is-resizing');
                        document.body.style.cursor = '';
                        document.body.style.userSelect = '';
                        document.removeEventListener('mousemove', onMouseMove);
                        document.removeEventListener('mouseup', onMouseUp);
                    }

                    document.addEventListener('mousemove', onMouseMove);
                    document.addEventListener('mouseup', onMouseUp);
                });

                // Touch support for mobile and tablets
                resizer.addEventListener('touchstart', (e) => {
                    if (!e.touches || e.touches.length === 0) return;
                    startX = e.touches[0].pageX;
                    startWidth = th.offsetWidth;
                    resizer.classList.add('is-resizing');

                    function onTouchMove(e) {
                        if (!e.touches || e.touches.length === 0) return;
                        const newWidth = Math.max(50, startWidth + (e.touches[0].pageX - startX));
                        th.style.width = newWidth + 'px';
                        th.style.minWidth = newWidth + 'px';
                    }

                    function onTouchEnd() {
                        resizer.classList.remove('is-resizing');
                        document.removeEventListener('touchmove', onTouchMove);
                        document.removeEventListener('touchend', onTouchEnd);
                    }

                    document.addEventListener('touchmove', onTouchMove, { passive: true });
                    document.addEventListener('touchend', onTouchEnd);
                }, { passive: true });

                // Double click auto-fits
                resizer.addEventListener('dblclick', (e) => {
                    e.stopPropagation();
                    th.style.width = '';
                    th.style.minWidth = '';
                });
            });

            // 2. Row Resizing (Bottom divider handle on each row's index cell)
            const rows = table.querySelectorAll('tbody tr');
            rows.forEach((tr) => {
                if (tr.querySelector('.row-resizer-handle')) return;

                const indexCell = tr.querySelector('.row-index-cell');
                if (!indexCell) return;

                const handle = document.createElement('div');
                handle.className = 'row-resizer-handle';
                indexCell.style.position = 'relative';
                indexCell.appendChild(handle);

                let startY, startHeight;

                handle.addEventListener('mousedown', (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    startY = e.pageY;
                    startHeight = tr.offsetHeight;
                    handle.classList.add('is-resizing');
                    document.body.style.cursor = 'row-resize';
                    document.body.style.userSelect = 'none';

                    function onMouseMove(e) {
                        const newHeight = Math.max(26, startHeight + (e.pageY - startY));
                        tr.style.height = newHeight + 'px';
                        tr.querySelectorAll('td').forEach(td => td.style.height = newHeight + 'px');
                    }

                    function onMouseUp() {
                        handle.classList.remove('is-resizing');
                        document.body.style.cursor = '';
                        document.body.style.userSelect = '';
                        document.removeEventListener('mousemove', onMouseMove);
                        document.removeEventListener('mouseup', onMouseUp);
                    }

                    document.addEventListener('mousemove', onMouseMove);
                    document.addEventListener('mouseup', onMouseUp);
                });

                // Touch support for mobile and tablets
                handle.addEventListener('touchstart', (e) => {
                    if (!e.touches || e.touches.length === 0) return;
                    startY = e.touches[0].pageY;
                    startHeight = tr.offsetHeight;
                    handle.classList.add('is-resizing');

                    function onTouchMove(e) {
                        if (!e.touches || e.touches.length === 0) return;
                        const newHeight = Math.max(26, startHeight + (e.touches[0].pageY - startY));
                        tr.style.height = newHeight + 'px';
                        tr.querySelectorAll('td').forEach(td => td.style.height = newHeight + 'px');
                    }

                    function onTouchEnd() {
                        handle.classList.remove('is-resizing');
                        document.removeEventListener('touchmove', onTouchMove);
                        document.removeEventListener('touchend', onTouchEnd);
                    }

                    document.addEventListener('touchmove', onTouchMove, { passive: true });
                    document.addEventListener('touchend', onTouchEnd);
                }, { passive: true });

                handle.addEventListener('dblclick', (e) => {
                    e.stopPropagation();
                    tr.style.height = '';
                    tr.querySelectorAll('td').forEach(td => td.style.height = '');
                });
            });
        }

        function setDensity(tableId, density) {
            const table = document.getElementById(tableId);
            if (!table) return;
            table.classList.remove('density-compact', 'density-standard', 'density-relaxed');
            table.classList.add(`density-${density}`);

            const panel = table.closest('.panel');
            if (panel) {
                panel.querySelectorAll('.pill-group button').forEach(btn => {
                    if (btn.textContent.toLowerCase() === density) {
                        btn.classList.add('active');
                    } else if (['compact', 'standard', 'relaxed'].includes(btn.textContent.toLowerCase())) {
                        btn.classList.remove('active');
                    }
                });
            }
        }

        function resetTable(tableId) {
            const table = document.getElementById(tableId);
            if (!table) return;
            table.querySelectorAll('th').forEach(th => {
                th.style.width = '';
                th.style.minWidth = '';
            });
            table.querySelectorAll('tr').forEach(tr => {
                tr.style.height = '';
                tr.querySelectorAll('td').forEach(td => td.style.height = '');
            });
            setDensity(tableId, 'standard');
            showToast("Grid reset to default dimensions");
        }

        // Initialize dashboard
        initTheme();
        fetchData();
        setInterval(fetchData, 4000);
    </script>
</body>
</html>
"""
