
import time
import warnings
import pandas as pd # Still imported in case pytrends returns DFs, though we use dicts mostly.

# Suppress warnings
warnings.filterwarnings("ignore")

try:
    from pytrends.request import TrendReq
except ImportError:
    print("pytrends not installed.")
    exit()

def get_rising_trends(seed_keywords, timeframe='today 12-m', geo='US'):
    """
    광범위한 시드 키워드(예: Skincare)를 기반으로 구글 트렌드에서 '급상승(Rising)' 검색어를 추출합니다.
    """
    pytrends = TrendReq(hl='en-US', tz=360)
    rising_dict = {}
    
    print(f"[{geo}] Google Trends Broad Discovery (Timeframe: {timeframe})...")
    
    for kw in seed_keywords:
        try:
            # cat=44: Beauty & Fitness category
            pytrends.build_payload([kw], cat=44, timeframe=timeframe, geo=geo, gprop='')
            related = pytrends.related_queries()
            if related and related[kw]['rising'] is not None:
                # rising 데이터프레임 가져오기
                df_rising = related[kw]['rising']
                # top 10만 추출
                top_rising = df_rising.head(10).to_dict('records') # [{'query': '...', 'value': ...}, ...]
                rising_dict[kw] = top_rising
                print(f"  - '{kw}': Found {len(top_rising)} rising terms")
            else:
                print(f"  - '{kw}': No rising terms found")
            
            time.sleep(2) # Rate limit 방지
        except Exception as e:
            print(f"  - '{kw}' Failed: {e}")
            time.sleep(5)
            
    return rising_dict

def main():
    print("=== Google Trends Broad Market Discovery Report ===\n")
    print("This report identifies rising related search queries for broad skincare topics.\n")

    # 1. 구글 트렌드 탐색 (시드 키워드 설정)
    seed_keywords = [
        'Skincare', 
        'Korean Skincare', 
        'Sunscreen', 
        'Face Serum', 
        'Moisturizer',
        'Toner pad' 
    ]
    
    # 최근 3개월 기준 (Fast Trend)
    rising_data = get_rising_trends(seed_keywords, timeframe='today 3-m', geo='US')
    
    if not rising_data:
        print("Failed to fetch Google Trends data.")
        return

def main():
    print("=== Google Trends Broad Market Discovery Report ===\n")
    print("This report identifies rising related search queries for broad skincare topics.\n")

    # 1. 구글 트렌드 탐색 (시드 키워드 설정)
    seed_keywords = [
        'Skincare', 
        'Korean Skincare', 
        'Sunscreen', 
        'Face Serum', 
        'Moisturizer',
        'Toner pad' 
    ]
    
    regions = ['US', 'JP']
    
    for geo in regions:
        print(f"\n" + "="*60)
        print(f"             GOOGLE TRENDS RISING QUERIES - {geo} (LAST 3 MONTHS)")
        print("="*60)
        
        # 최근 3개월 기준 (Fast Trend)
        rising_data = get_rising_trends(seed_keywords, timeframe='today 3-m', geo=geo)
        
        if not rising_data:
            print(f"No rising data found for {geo}.")
            continue

        for category, trends in rising_data.items():
            print(f"\n[{category}] Rising Related Queries:")
            if not trends:
                print("  (None)")
                continue
            for item in trends:
                # value는 상승률(%) 또는 'Breakout'(급상승)
                val = item['value']
                print(f"  - {item['query']} (Growth: {val}%)")
        
        # 쿨다운 (지역 간)
        time.sleep(5)

    print("\n" + "="*60)
    print("End of Report")

if __name__ == "__main__":
    main()
