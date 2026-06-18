
import pandas as pd
import time
import json
import warnings
from datetime import datetime

# Suppress warnings
warnings.filterwarnings("ignore")

try:
    from pytrends.request import TrendReq
except ImportError:
    print("pytrends not installed. Please install it using 'pip install pytrends'")
    exit()

# === TARGET SKINCARE KEYWORDS ===
# 구글 트렌드에서 조회할 핵심 키워드 리스트
TARGET_KEYWORDS = [
    # 1. Product Types
    "Sun Serum", "Sun Stick", "Toner Pad", "Modeling Mask", "Sheet Mask", 
    "Cushion Foundation", "Face Serum", "Moisturizer",
    
    # 2. Key Ingredients
    "Retinol", "Cica", "Glutathione", "Hyaluronic Acid", "Panthenol", 
    "Heartleaf", "Bakuchiol", "Snail Mucin", "Rice Water",
    
    # 3. Concerns/Trends
    "Barrier Repair", "Glass Skin", "Reef Safe", "White Cast"
]

import random

def get_google_trend_stats(keywords, timeframe='today 3-m', geo='US'):
    """
    Fetch Interest Over Time from Google Trends for specified keywords.
    Returns a list of dicts with keyword, volume, and growth.
    Includes robust retry logic to handle 429 Too Many Requests errors.
    """
    pytrends = TrendReq(hl='en-US', tz=360, retries=2, backoff_factor=0.5)
    results = []
    
    print(f"Fetching Google Trends data for {len(keywords)} keywords ({timeframe})...")
    
    for kw in keywords:
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Add random jitter to simple sleep to look more human
                sleep_time = random.uniform(3, 6) + (attempt * 5) # 3-6s, then 8-11s, 13-16s
                time.sleep(sleep_time)

                # cat=44: Beauty & Fitness category
                pytrends.build_payload([kw], cat=44, timeframe=timeframe, geo=geo, gprop='')
                data = pytrends.interest_over_time()
                
                if not data.empty and kw in data.columns:
                    recent_window = data[kw].tail(14)
                    past_window = data[kw].head(14)
                    
                    current_vol = recent_window.mean()
                    past_vol = past_window.mean()
                    
                    if past_vol == 0:
                        growth = 100.0 if current_vol > 0 else 0.0
                    else:
                        growth = ((current_vol - past_vol) / past_vol) * 100
                    
                    status = 'Stable'
                    if growth >= 50:
                        status = 'HOT'
                    elif growth >= 20:
                        status = 'Rising'
                    elif past_vol == 0 and current_vol > 10:
                        status = 'NEW'
                        
                    results.append({
                        'keyword': kw,
                        'count': int(round(current_vol)),
                        'growth': round(growth, 1),
                        'status': status
                    })
                    print(f"  - [Success] {kw}: Vol={int(round(current_vol))}, Growth={round(growth,1)}%")
                else:
                    print(f"  - [No Data] {kw}")
                
                break # Success, exit retry loop
                
            except Exception as e:
                if "429" in str(e):
                    print(f"  - [429 Error] {kw} (Attempt {attempt+1}/{max_retries}). Backing off...")
                else:
                    print(f"  - [Error] {kw}: {e}")
                    
                if attempt == max_retries - 1:
                    print(f"  - [Failed] Giving up on {kw}")
            
    return results

def main():
    print("=== Google Trends Global Ranking Generator ===\n")
    
def main():
    print("=== Google Trends Global Ranking Generator ===\n")
    
    regions = ['US', 'JP']
    
    for geo in regions:
        print(f"\n--- Processing Region: {geo} ---")
        
        # 1. Fetch Data
        trend_data = get_google_trend_stats(TARGET_KEYWORDS, timeframe='today 3-m', geo=geo)
        
        if not trend_data:
            print(f"No trend data fetched for {geo}.")
            # Save empty placeholder or continue
            continue

        # 2. Rank by 'count' and Growth
        ranked_trends = sorted(trend_data, key=lambda x: (x['count'], x['growth']), reverse=True)
        
        # 3. Output to Console
        print("\n" + "="*50)
        print(f"       SKINCARE TREND RANKING ({geo})")
        print("="*50)
        
        for i, item in enumerate(ranked_trends[:10], 1):
            mark = f"[{item['status']}]" if item['status'] in ['HOT', 'NEW'] else ""
            print(f"{i}. {item['keyword']} {mark}")
            print(f"   (Interest: {item['count']}, Growth: {item['growth']}%)")
            
        # 4. Save to JSON for UI
        ui_data = {
            "title": f"Skincare Trend Ranking ({geo})",
            "region": geo,
            "source": "Google Trends (Last 3 months)",
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "ranking": ranked_trends[:10]
        }
        
        output_filename = f"ranking_{geo}_{datetime.now().strftime('%Y-%m-%d')}.json"
        with open(output_filename, 'w', encoding='utf-8') as f:
            json.dump(ui_data, f, indent=2)
        
        print(f"\n[Success] Ranking data saved to {output_filename}")
        
        # Long sleep between regions to prevent rate limits
        print("Sleeping 10s before next region...")
        time.sleep(10)

if __name__ == "__main__":
    main()
