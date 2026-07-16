import os
import psycopg2
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

def get_connection():
    return psycopg2.connect(
        host=os.getenv('DB_HOST'),
        port=os.getenv('DB_PORT'),
        dbname=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD')
    )

def get_latest_run_summary(cur):
    cur.execute("""
        SELECT 
            a.name,
            i.id,
            i.run_at,
            i.finished_at,
            i.count,
            i.status,
            EXTRACT(EPOCH FROM (i.finished_at - i.run_at)) AS runtime_seconds
        FROM ingestion_run i
        JOIN app a ON i.app_id = a.id
        WHERE i.id IN (
            SELECT id FROM ingestion_run 
            ORDER BY run_at DESC 
            LIMIT 20
        )
        ORDER BY a.name
    """)
    return cur.fetchall()

def get_flag_summary(cur):
    cur.execute("""
        SELECT 
            qf.flag_type,
            COUNT(*) as count
        FROM quality_flag qf
        JOIN raw_review r ON qf.review_id = r.review_id
        JOIN ingestion_run i ON r.ingestion_run_id = i.id
        WHERE i.id IN (
            SELECT id FROM ingestion_run 
            ORDER BY run_at DESC 
            LIMIT 20
        )
        GROUP BY qf.flag_type
        ORDER BY count DESC
    """)
    return cur.fetchall()

def get_db_growth(cur):
    cur.execute("""
        SELECT COUNT(*) FROM raw_review r
        JOIN ingestion_run i ON r.ingestion_run_id = i.id
        WHERE i.id IN (
            SELECT id FROM ingestion_run 
            ORDER BY run_at DESC 
            LIMIT 20
        )
    """)
    return cur.fetchone()[0]

def get_table_counts(cur):
    cur.execute("SELECT COUNT(*) FROM raw_review")
    raw = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM cleaned_review")
    cleaned = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM quality_flag")
    flags = cur.fetchone()[0]
    cur.execute("""
        SELECT COUNT(*) FROM raw_review r
        LEFT JOIN ingestion_run i ON r.ingestion_run_id = i.id
        WHERE i.id IS NULL
    """)
    orphans = cur.fetchone()[0]
    return raw, cleaned, flags, orphans

def determine_health(runs, flag_summary, orphans, raw, cleaned):
    issues = []
    warnings = []

    # Check for failed apps
    failed_apps = [r for r in runs if r[5] == 'failed']
    if failed_apps:
        issues.append(f"{len(failed_apps)} app(s) failed: {', '.join(r[0] for r in failed_apps)}")

    # Check table relationship
    if raw != cleaned:
        issues.append(f"raw_review ({raw}) != cleaned_review ({cleaned})")
    if orphans > 0:
        issues.append(f"{orphans} orphan reviews found")

    # Check flag rates
    total_reviewed = sum(r[4] for r in runs)
    flag_counts = {f[0]: f[1] for f in flag_summary}
    low_signal_rate = flag_counts.get('low_signal', 0) / max(total_reviewed, 1)
    duplicate_rate = flag_counts.get('duplicate', 0) / max(total_reviewed, 1)

    if low_signal_rate > 0.6:
        warnings.append(f"High low-signal rate: {low_signal_rate:.1%}")
    if duplicate_rate > 0.3:
        warnings.append(f"High duplicate rate: {duplicate_rate:.1%}")

    # Check for apps with no finished_at
    incomplete = [r for r in runs if r[3] is None]
    if incomplete:
        warnings.append(f"{len(incomplete)} app(s) missing finished_at")

    if issues:
        return "FAILING", issues, warnings
    elif warnings:
        return "WARNING", issues, warnings
    else:
        return "HEALTHY", issues, warnings

def generate_report(runs, flag_summary, raw, cleaned, flags, orphans, new_records):
    now = datetime.now()
    timestamp = now.strftime("%Y%m%d_%H%M%S")

    # Get run time info
    run_at = runs[0][2] if runs else now
    finished_at = max(r[3] for r in runs if r[3]) if any(r[3] for r in runs) else now
    total_runtime = sum(r[6] for r in runs if r[6]) 

    health_status, issues, warnings = determine_health(runs, flag_summary, orphans, raw, cleaned)

    total_fetched = sum(r[4] for r in runs)
    failed_apps = [r for r in runs if r[5] == 'failed']
    flag_counts = {f[0]: f[1] for f in flag_summary}

    lines = []
    lines.append(f"# Pipeline Run Summary")
    lines.append(f"**Generated:** {now.strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"**Status:** {health_status}")
    lines.append("")

    lines.append("## Run Info")
    lines.append(f"- **Start time:** {run_at.strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"- **Finish time:** {finished_at.strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"- **Total runtime:** {total_runtime:.1f} seconds")
    lines.append("")

    lines.append("## Ingestion Results")
    lines.append(f"- **Total fetched:** {total_fetched:,}")
    lines.append(f"- **Total inserted (new records):** {new_records:,}")
    lines.append(f"- **Total skipped (duplicates):** {total_fetched - new_records:,}")
    lines.append(f"- **Failed apps:** {len(failed_apps) if failed_apps else 'None'}")
    lines.append("")

    lines.append("## Quality Flags")
    for flag_type, count in flag_summary:
        pct = count / max(total_fetched, 1) * 100
        lines.append(f"- **{flag_type}:** {count:,} ({pct:.1f}%)")
    lines.append("")

    lines.append("## Table Validation")
    lines.append(f"- **raw_review count:** {raw:,}")
    lines.append(f"- **cleaned_review count:** {cleaned:,}")
    lines.append(f"- **raw == cleaned:** {raw == cleaned}")
    lines.append(f"- **Orphan reviews:** {orphans}")
    lines.append("")

    lines.append("## Database Growth")
    lines.append(f"- **New records this run:** {new_records:,}")
    lines.append(f"- **Total records in database:** {raw:,}")
    lines.append("")

    lines.append("## Per-App Report")
    lines.append(f"| {'App':<20} | {'Count':>6} | {'Runtime(s)':>10} | {'Status':>8} |")
    lines.append(f"|{'-'*22}|{'-'*8}|{'-'*12}|{'-'*10}|")
    for r in runs:
        runtime = f"{r[6]:.1f}" if r[6] else "N/A"
        lines.append(f"| {r[0]:<20} | {r[4]:>6} | {runtime:>10} | {r[5]:>8} |")
    lines.append("")

    if issues or warnings:
        lines.append("## Issues and Warnings")
        for issue in issues:
            lines.append(f"- [ISSUE] {issue}")
        for warning in warnings:
            lines.append(f"- [WARNING] {warning}")
        lines.append("")

    return "\n".join(lines), timestamp

def main():
    conn = get_connection()
    cur = conn.cursor()

    runs = get_latest_run_summary(cur)
    flag_summary = get_flag_summary(cur)
    raw, cleaned, flags, orphans = get_table_counts(cur)
    new_records = get_db_growth(cur)

    report, timestamp = generate_report(
        runs, flag_summary, raw, cleaned, flags, orphans, new_records
    )

    # Save to file
    os.makedirs('monitoring', exist_ok=True)
    filename = f"monitoring/run_summary_{timestamp}.md"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(report)

    print(report)
    print(f"\nReport saved to: {filename}")

    cur.close()
    conn.close()

if __name__ == "__main__":
    main()