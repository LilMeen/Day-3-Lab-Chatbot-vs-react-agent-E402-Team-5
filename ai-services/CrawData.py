import requests
from bs4 import BeautifulSoup
import json

BASE_URL = "https://cinestar.com.vn"

def get_all_movies():
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(BASE_URL, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        script_tag = soup.find('script', id='__NEXT_DATA__')
        
        full_data = json.loads(script_tag.string)
        res = full_data.get('props', {}).get('pageProps', {}).get('res', {})
        
        raw_list = res.get('listMovie', []) + res.get('listComingMovie', [])
        
        final_results = []
        for movie in raw_list:
            final_results.append({
                "movie_id": movie.get('id'),
                "movie_url": f"{BASE_URL}/phim/{movie.get('id')}",
                "movie_name": movie.get('name_vn'),
                "image": movie.get('image'),
                "category": movie.get('type_name_vn'),
                "description": movie.get('brief_vn'),
                "director": movie.get('director'),
                "cast": movie.get('actor'), 
                "time": movie.get('time'),
                "release_date": movie.get('release_date'),
                "status": "Đang chiếu" if movie in res.get('listMovie', []) else "Sắp chiếu"
            })
        return final_results
    except Exception as e:
        return {"error": f"Lỗi get_all_movies: {str(e)}"}

def get_movie_details(movie_id, all_movies_list):
    for movie in all_movies_list:
        if movie['movie_id'] == movie_id:
            return movie
    return {"error": "Không tìm thấy phim"}

def get_discount():
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(BASE_URL, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        script_tag = soup.find('script', id='__NEXT_DATA__')
        
        full_data = json.loads(script_tag.string)
        promo_data = full_data.get('props', {}).get('pageProps', {}).get('listPromotion', {}).get('listPromotion', [])
        
        results = []
        for promo in promo_data:
            results.append({
                "discount_name": promo.get('name'),
                "discount_link": promo.get('link'),
                "image": promo.get('media')
            })
        return results
    except Exception as e:
        return {"error": f"Lỗi get_discount: {str(e)}"}
