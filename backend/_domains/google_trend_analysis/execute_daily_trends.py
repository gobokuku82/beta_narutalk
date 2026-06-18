
import schedule
import time
import subprocess
import datetime
import os

def job():
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    print(f"\n[Scheduler] Starting daily trend analysis job for {today}...")

    # 1. Run Google Trend Analysis
    try:
        print("[Scheduler] Running Google Trend Analysis (get_trend.py)...")
        # Force UTF-8 encoding for the subprocess output
        env = os.environ.copy()
        env["PYTHONUTF8"] = "1"
        
        with open(f"trend_report_{today}.txt", "w", encoding="utf-8") as f:
            subprocess.run(["python", "get_trend.py"], stdout=f, check=True, env=env)
        print(f"  -> Report saved to trend_report_{today}.txt")
    except Exception as e:
        print(f"  -> Error running get_trend.py: {e}")

    # 2. Run Ranking Analysis
    try:
        print("[Scheduler] Running Global Ranking Analysis (rank_trend.py)...")
        # rank_trend.py saves the JSON file internally. 
        # Here we capture the console log (text table) to a log file.
        with open(f"ranking_log_{today}.txt", "w", encoding="utf-8") as f:
            subprocess.run(["python", "rank_trend.py"], stdout=f, check=True, env=env)
        print(f"  -> Process log saved to ranking_log_{today}.txt")
    except Exception as e:
        print(f"  -> Error running rank_trend.py: {e}")

    print(f"[Scheduler] Job completed for {today}.\n")

def main():
    print("=== Trend Analysis Scheduler ===")
    print("Scheduled to run daily at 09:00.")
    print("Press Ctrl+C to exit.")
    
    # Schedule the job daily at 09:00
    schedule.every().day.at("09:00").do(job)
    
    # Also run once immediately for verification? 
    # Uncomment next line to run immediately on startup
    
    job()

    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    main()
