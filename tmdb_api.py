import os
import requests
from dotenv import load_dotenv
from langchain_ollama import ChatOllama

load_dotenv()
TMDB_API_KEY = os.getenv("TMDB_API_KEY")
BASE_URL = "https://api.themoviedb.org/3"

# Dilden bağımsız standart tür kodları
GENRE_MAP = {"comedy": 35, "scifi": 878, "drama": 18, "arthouse": 18, "thriller": 53, "festival": 18}

TMDB_LANGS = {
    "US": "en-US", "GB": "en-GB", "TR": "tr-TR", "DE": "de-DE", 
    "ES": "es-ES", "BR": "pt-BR", "RU": "ru-RU", "AE": "ar-AE", 
    "CN": "zh-CN", "JP": "ja-JP"
}

# Her ülkenin yerel dilleri ve ülke kodları
REGION_ORIGIN_CONFIG = {
    "TR": {"langs": ["tr"], "country": "TR"},
    "US": {"langs": ["en"], "country": "US"},
    "GB": {"langs": ["en"], "country": "GB"},
    "DE": {"langs": ["de"], "country": "DE"},
    "ES": {"langs": ["es", "ca", "gl", "eu"], "country": "ES"},
    "BR": {"langs": ["pt"], "country": "BR"},
    "RU": {"langs": ["ru"], "country": "RU"},
    "AE": {"langs": ["ar"], "country": "AE"},
    "CN": {"langs": ["zh", "cn", "yue"], "country": "CN"},
    "JP": {"langs": ["ja"], "country": "JP"}
}

PLATFORM_ALIASES = {
    "prime video": "Amazon Prime Video", "amazon": "Amazon Prime Video",
    "disney plus": "Disney+", "apple tv plus": "Apple TV+", "apple tv": "Apple TV+",
    "hbo max": "Max", "paramount plus": "Paramount+", "shahid vip": "Shahid",
    "osn": "OSN+", "bbc iplayer": "BBC iPlayer", "channel 4": "Channel 4",
    "movistar plus+": "Movistar Plus+", "movistar+": "Movistar Plus+",
    "kinopoisk": "Kinopoisk", "ivi": "Ivi", "okko": "Okko", "iqiyi": "iQIYI",
    "tencent": "Tencent Video", "youku": "Youku", "bilibili": "Bilibili",
    "u-next": "U-NEXT", "abema": "AbemaTV", "abematv": "AbemaTV", "dtv": "dTV",
    "wow": "WOW", "joyn": "Joyn", "rtl+": "RTL+", "globoplay": "Globoplay",
    "crunchyroll": "Crunchyroll"
}

def translate_keyword_dynamically(keyword):
    if not keyword or not keyword.strip(): return ""
    try:
        llm = ChatOllama(model="llama3", temperature=0.0)
        return llm.invoke(f"Translate this topic to 1-2 standard English keywords. Reply ONLY with the words:\n{keyword}").content.strip().lower()
    except Exception: return keyword.strip().lower()

def get_person_id(name):
    if not name: return None
    try:
        res = requests.get(f"{BASE_URL}/search/person", params={"api_key": TMDB_API_KEY, "query": name}).json()
        if res.get("results"): return res["results"][0]["id"]
    except Exception: pass
    return None

def get_tmdb_keyword_ids(query):
    try:
        res = requests.get(f"{BASE_URL}/search/keyword", params={"api_key": TMDB_API_KEY, "query": query, "page": 1}).json()
        return [str(k["id"]) for k in res.get("results", [])[:3]]
    except Exception: return []

def get_streaming_platforms(content_id, region="TR", tmdb_type="movie"):
    try:
        res = requests.get(f"{BASE_URL}/{tmdb_type}/{content_id}/watch/providers", params={"api_key": TMDB_API_KEY}).json()
        if region in res.get("results", {}):
            return [p["provider_name"] for p in res["results"][region].get("flatrate", [])]
    except Exception: pass
    return []

def match_user_platforms(movie_platforms, user_subscriptions):
    matched = []
    user_subs_clean = [s.lower().strip() for s in user_subscriptions]
    for mp in movie_platforms:
        mp_lower = mp.lower()
        for sub in user_subs_clean:
            if sub in mp_lower or mp_lower in sub or any(alias in mp_lower for alias, target in PLATFORM_ALIASES.items() if target.lower() == sub):
                matched.append(mp)
                break
    return list(dict.fromkeys(matched))

def search_content(user_profile, limit=16):
    if not isinstance(user_profile, dict): return []
    region = user_profile.get("region", "TR")
    tmdb_lang = TMDB_LANGS.get(region, "tr-TR")
    user_subscriptions = user_profile.get("subscriptions", [])
    raw_keyword = user_profile.get("keywords", "").strip()

    internal_ctype = user_profile.get("content_type", "movie")
    internal_genres = user_profile.get("genres", [])
    origin_filter = user_profile.get("origin", "all") # 'all', 'local', 'international'
    
    origin_cfg = REGION_ORIGIN_CONFIG.get(region, {"langs": ["tr"], "country": "TR"})
    local_langs = origin_cfg["langs"]
    local_country = origin_cfg["country"]

    tmdb_type = "movie"
    extra_genre_ids = []
    extra_params = {}

    if internal_ctype == "tv":
        tmdb_type = "tv"
    elif internal_ctype == "documentary":
        tmdb_type = "movie"
        extra_genre_ids.append("99")
    elif internal_ctype == "animation":
        tmdb_type = "movie"
        extra_genre_ids.append("16")
    elif internal_ctype == "anime":
        tmdb_type = "tv"
        extra_genre_ids.append("16")
        extra_params["with_original_language"] = "ja"
    elif internal_ctype == "short":
        tmdb_type = "movie"
        extra_params["with_runtime.lte"] = "40"

    genre_ids = [str(GENRE_MAP[g]) for g in internal_genres if g in GENRE_MAP]
    all_genres = list(set(genre_ids + extra_genre_ids))
    with_genres = ",".join(all_genres)

    raw_candidates = []
    seen_ids = set()

    # KESİN MENŞE KONTROLÜ
    def is_origin_valid(item):
        orig_lang = str(item.get("original_language", "")).lower()
        orig_countries = item.get("origin_country", [])

        # Yerel Yapım Kontrolü
        is_local = (orig_lang in local_langs) or (local_country in orig_countries)

        if origin_filter == "local":
            return is_local
        elif origin_filter == "international":
            return not is_local
        return True

    def add_unique(item):
        i_id = item.get("id")
        if i_id and i_id not in seen_ids:
            if not is_origin_valid(item):
                return  # Kurala uymayan yapımı kesinlikle listeye alma
            
            seen_ids.add(i_id)
            item["norm_title"] = item.get("title") or item.get("name") or item.get("original_title") or item.get("original_name", "Unknown")
            item["norm_date"] = item.get("release_date") or item.get("first_air_date", "Unknown")
            raw_candidates.append(item)

    # 1. KULLANICI KELİME ARATTIYSA
    if raw_keyword:
        # A) Doğrudan Arama
        en_keyword = translate_keyword_dynamically(raw_keyword)
        for term in [raw_keyword, en_keyword]:
            try:
                res = requests.get(f"{BASE_URL}/search/{tmdb_type}", params={"api_key": TMDB_API_KEY, "query": term, "language": tmdb_lang, "page": 1}).json()
                for item in res.get("results", []): add_unique(item)
            except: pass

        # B) Konu Etiketi ile Discover Taraması
        keyword_ids = []
        for term in [raw_keyword, en_keyword]: keyword_ids.extend(get_tmdb_keyword_ids(term))
        if keyword_ids:
            try:
                params = {
                    "api_key": TMDB_API_KEY, 
                    "language": tmdb_lang, 
                    "sort_by": "popularity.desc", 
                    "with_keywords": "|".join(set(keyword_ids)), 
                    "page": 1
                }
                params.update(extra_params)
                if origin_filter == "local" and internal_ctype != "anime":
                    params["with_original_language"] = local_langs[0]

                res = requests.get(f"{BASE_URL}/discover/{tmdb_type}", params=params).json()
                for item in res.get("results", []): add_unique(item)
            except: pass

    # 2. GENEL KEŞİF VEYA YERLİ HAVUZU BESLEME
    # Eğer kullanıcı "Yerli Yapım" istediyse, havuzun boş kalmaması için Discover'dan yerli yapımları çek
    if not raw_candidates or not raw_keyword:
        params = {
            "api_key": TMDB_API_KEY, 
            "language": tmdb_lang, 
            "sort_by": "popularity.desc", 
            "watch_region": region, 
            "with_genres": with_genres
        }
        params.update(extra_params)
        
        if origin_filter == "local" and internal_ctype != "anime":
            params["with_original_language"] = local_langs[0]
        elif origin_filter == "international" and internal_ctype != "anime":
            params["without_original_language"] = local_langs[0]

        if "festival" in internal_genres: params["vote_count.gte"] = 100
        try:
            res = requests.get(f"{BASE_URL}/discover/{tmdb_type}", params=params).json()
            for item in res.get("results", []): add_unique(item)
        except: pass

    final_movies = []
    for item in raw_candidates:
        platforms = get_streaming_platforms(item.get("id"), region=region, tmdb_type=tmdb_type)
        matched = match_user_platforms(platforms, user_subscriptions)
        if matched: 
            final_movies.append({
                "id": item.get("id"), "title": item.get("norm_title"),
                "overview": item.get("overview") or "", "poster_path": item.get("poster_path"),
                "release_date": item.get("norm_date"), "vote_average": item.get("vote_average", 0),
                "matched_platforms": matched
            })
        if len(final_movies) >= limit: break

    return final_movies