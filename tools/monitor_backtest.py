#!/usr/bin/env python3
"""
Real-time Backtest Monitor
Displays backtest progress in terminal with live updates
"""
import os
import time
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

LOG_FILE = "/tmp/comprehensive_backtest_relaxed.log"
TOTAL_SYMBOLS = 5575
CHECK_INTERVAL = 5  # seconds

def clear_screen():
    """Clear terminal screen"""
    os.system('clear' if os.name == 'posix' else 'cls')

def get_backtest_stats():
    """Extract stats from log file"""
    if not os.path.exists(LOG_FILE):
        return None

    stats = {
        'total_analyzed': 0,
        'beta_rejections': 0,
        'data_failures': 0,
        'trades_found': 0,
        'current_symbol': 'Unknown',
        'log_size_mb': 0,
        'symbols_with_trades': []
    }

    try:
        # Get log file size
        stats['log_size_mb'] = os.path.getsize(LOG_FILE) / (1024 * 1024)

        # Count various metrics
        with open(LOG_FILE, 'r') as f:
            # Read last 1000 lines for current symbol
            lines = f.readlines()
            recent_lines = lines[-1000:] if len(lines) > 1000 else lines

            # Find current symbol
            for line in reversed(recent_lines):
                if 'Analyzing' in line and '.NS' in line:
                    try:
                        parts = line.split('Analyzing')[1].split('-')[0].strip()
                        stats['current_symbol'] = parts
                        break
                    except:
                        pass

        # Use grep for fast counting
        try:
            stats['total_analyzed'] = int(subprocess.check_output(
                f"grep -c 'Analyzing.*\\.NS' {LOG_FILE} 2>/dev/null || echo 0",
                shell=True
            ).decode().strip())
        except:
            pass

        try:
            stats['beta_rejections'] = int(subprocess.check_output(
                f"grep -c 'Beta too low' {LOG_FILE} 2>/dev/null || echo 0",
                shell=True
            ).decode().strip())
        except:
            pass

        try:
            stats['data_failures'] = int(subprocess.check_output(
                f"grep -c 'No data available' {LOG_FILE} 2>/dev/null || echo 0",
                shell=True
            ).decode().strip())
        except:
            pass

        # Check for trades
        try:
            trades_output = subprocess.check_output(
                f"grep 'Trades:' {LOG_FILE} | grep -v 'Trades: 0' 2>/dev/null || echo ''",
                shell=True
            ).decode().strip()

            if trades_output:
                stats['trades_found'] = len(trades_output.split('\n'))
                stats['symbols_with_trades'] = trades_output.split('\n')[:5]  # First 5
        except:
            pass

    except Exception as e:
        print(f"Error reading log: {e}")

    return stats

def get_process_info():
    """Check if backtest process is running"""
    try:
        result = subprocess.check_output(
            "ps aux | grep '[p]ython.*cli.py analyze' | grep -v grep",
            shell=True
        ).decode().strip()

        if result:
            # Extract PID and elapsed time
            parts = result.split()
            pid = parts[1]

            # Get process start time
            etime = subprocess.check_output(
                f"ps -p {pid} -o etime= 2>/dev/null || echo '00:00'",
                shell=True
            ).decode().strip()

            return {
                'running': True,
                'pid': pid,
                'elapsed': etime
            }
    except:
        pass

    return {'running': False}

def format_time_remaining(analyzed, total, elapsed_seconds):
    """Estimate time remaining"""
    if analyzed == 0:
        return "Calculating..."

    rate = analyzed / elapsed_seconds  # symbols per second
    remaining_symbols = total - analyzed

    if rate > 0:
        remaining_seconds = remaining_symbols / rate
        hours = int(remaining_seconds // 3600)
        minutes = int((remaining_seconds % 3600) // 60)
        return f"{hours}h {minutes}m"

    return "Unknown"

def parse_elapsed_time(etime_str):
    """Convert ps etime format to seconds"""
    try:
        parts = etime_str.strip().split(':')
        if len(parts) == 2:  # MM:SS
            return int(parts[0]) * 60 + int(parts[1])
        elif len(parts) == 3:  # HH:MM:SS
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        elif '-' in etime_str:  # DD-HH:MM:SS
            days_part, time_part = etime_str.split('-')
            time_parts = time_part.split(':')
            return (int(days_part) * 86400 +
                   int(time_parts[0]) * 3600 +
                   int(time_parts[1]) * 60 +
                   int(time_parts[2]))
    except:
        pass
    return 0

def main():
    """Main monitoring loop"""
    print("Starting backtest monitor...")
    print("Press Ctrl+C to exit\n")
    time.sleep(2)

    try:
        while True:
            clear_screen()

            # Header
            print("=" * 80)
            print(" " * 20 + "COMPREHENSIVE BACKTEST MONITOR")
            print("=" * 80)
            print()

            # Process status
            proc_info = get_process_info()

            if proc_info['running']:
                print(f"📊 Status: RUNNING (PID: {proc_info['pid']})")
                print(f"⏱️  Elapsed Time: {proc_info['elapsed']}")
            else:
                print("📊 Status: NOT RUNNING or COMPLETED")
                print("⚠️  Check if backtest finished or crashed")

            print()

            # Backtest statistics
            stats = get_backtest_stats()

            if stats:
                # Progress
                progress_pct = (stats['total_analyzed'] / TOTAL_SYMBOLS) * 100
                unique_symbols = stats['total_analyzed'] // 2  # Rough estimate (each symbol analyzed multiple times in walk-forward)

                print(f"📈 Progress:")
                print(f"   Total Analyses: {stats['total_analyzed']:,}")
                print(f"   Unique Symbols (est): {unique_symbols:,} / {TOTAL_SYMBOLS:,}")
                print(f"   Progress: {progress_pct:.1f}%")

                # Progress bar
                bar_width = 50
                filled = int(bar_width * progress_pct / 100)
                bar = '█' * filled + '░' * (bar_width - filled)
                print(f"   [{bar}] {progress_pct:.1f}%")
                print()

                # Time estimate
                if proc_info['running']:
                    elapsed_sec = parse_elapsed_time(proc_info['elapsed'])
                    if elapsed_sec > 0:
                        eta = format_time_remaining(unique_symbols, TOTAL_SYMBOLS, elapsed_sec)
                        print(f"⏳ Estimated Time Remaining: {eta}")
                        print()

                # Current symbol
                print(f"🔍 Current Symbol: {stats['current_symbol']}")
                print()

                # Rejection stats
                print(f"📉 Rejection Statistics:")
                print(f"   Beta < 1.2: {stats['beta_rejections']:,} ({stats['beta_rejections']/max(stats['total_analyzed'],1)*100:.1f}%)")
                print(f"   Data Failures: {stats['data_failures']:,} ({stats['data_failures']/max(stats['total_analyzed'],1)*100:.1f}%)")
                passing = stats['total_analyzed'] - stats['beta_rejections'] - stats['data_failures']
                print(f"   Passing Filters: {passing:,} ({passing/max(stats['total_analyzed'],1)*100:.1f}%)")
                print()

                # Trades found (CRITICAL METRIC)
                if stats['trades_found'] > 0:
                    print(f"✅ TRADES FOUND: {stats['trades_found']} symbols generated trades!")
                    print(f"   Symbols with trades:")
                    for trade_line in stats['symbols_with_trades']:
                        print(f"   - {trade_line[:100]}")
                else:
                    print(f"❌ Trades Found: 0 (still searching...)")

                print()

                # File info
                print(f"📁 Log File: {LOG_FILE}")
                print(f"   Size: {stats['log_size_mb']:.1f} MB")
                print()

            else:
                print("⚠️  No log file found. Backtest may not have started.")
                print(f"   Expected location: {LOG_FILE}")
                print()

            # Footer
            print("=" * 80)
            print(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"Next update in {CHECK_INTERVAL} seconds... (Ctrl+C to exit)")

            time.sleep(CHECK_INTERVAL)

    except KeyboardInterrupt:
        clear_screen()
        print("\n👋 Monitor stopped by user")
        print("\nFinal Statistics:")
        stats = get_backtest_stats()
        if stats:
            print(f"  Total Analyzed: {stats['total_analyzed']:,}")
            print(f"  Beta Rejections: {stats['beta_rejections']:,}")
            print(f"  Trades Found: {stats['trades_found']}")
        print()

if __name__ == '__main__':
    main()
