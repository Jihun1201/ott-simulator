import requests
import json

API_KEY = "5fbb185abbffb48f3e8a74f243b0ce47"
IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w500"

# 다큐멘터리(99) 제거 완료!
categories = [
    {"name": "인기 영화", "url": "https://api.themoviedb.org/3/movie/popular", "params": {}},
    {"name": "한국 드라마", "url": "https://api.themoviedb.org/3/discover/tv", "params": {"with_original_language": "ko", "with_genres": "18"}},
    {"name": "미국 드라마", "url": "https://api.themoviedb.org/3/discover/tv", "params": {"with_original_language": "en", "with_genres": "18"}},
    {"name": "일본 드라마", "url": "https://api.themoviedb.org/3/discover/tv", "params": {"with_original_language": "ja", "with_genres": "18", "without_genres": "16"}},
    {"name": "일본 애니메이션", "url": "https://api.themoviedb.org/3/discover/tv", "params": {"with_original_language": "ja", "with_genres": "16"}},
    {"name": "한국 예능", "url": "https://api.themoviedb.org/3/discover/tv", "params": {"with_original_language": "ko", "with_genres": "10764|10767"}}
]

ultimate_data = []
print("🚀 대용량 종합 OTT 데이터 추출을 시작합니다...\n")

for category in categories:
    url = category["url"]
    items_collected = 0
    page_num = 1
    
    while items_collected < 60:
        params = category["params"].copy()
        params.update({"api_key": API_KEY, "language": "ko-KR", "page": page_num})
        response = requests.get(url, params=params)
        
        if response.status_code == 200:
            results = response.json().get("results", [])
            for item in results:
                if items_collected >= 60: break
                
                unified_title = item.get("title") or item.get("name")
                poster_path = item.get("poster_path")
                full_poster_url = f"{IMAGE_BASE_URL}{poster_path}" if poster_path else None
                
                # ⭐ 줄거리(overview) 필수 추출 부분!
                content_info = {
                    "title": unified_title,
                    "overview": item.get("overview", "등록된 줄거리 정보가 없습니다."), 
                    "genre_ids": item.get("genre_ids", []),
                    "poster_path": full_poster_url,
                    "vote_average": item.get("vote_average", 0),
                    "category_type": category["name"]
                }
                
                ultimate_data.append(content_info)
                items_collected += 1
            page_num += 1
        else:
            break
            
    print(f"✅ {category['name']} 추출 완료! (총 {items_collected}개)")

with open("ultimate_ott_data.json", "w", encoding="utf-8") as f:
    json.dump(ultimate_data, f, ensure_ascii=False, indent=4)

print(f"\n🎉 총 {len(ultimate_data)}개의 데이터가 성공적으로 저장되었습니다!")