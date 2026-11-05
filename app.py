import streamlit as st
from ai_agent import generate_recommendation
from tmdb_api import search_content
from database import record_feedback, get_user_memory

st.set_page_config(page_title="EntertainmentAI", page_icon="🍿", layout="wide")

st.markdown("""
<style>
    .title-logo { font-size: 3.2rem; font-weight: 900; background: -webkit-linear-gradient(45deg, #E50914, #B20710); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: -15px; }
    .subtitle { color: #A0AAB2; font-size: 1.1rem; margin-bottom: 30px; }
    div[data-testid="stVerticalBlock"] > div[style*="border"] { border-radius: 12px; background-color: #161A22 !important; border: 1px solid #2D333B !important; transition: all 0.3s ease; padding: 15px; }
    div[data-testid="stVerticalBlock"] > div[style*="border"]:hover { transform: translateY(-5px); box-shadow: 0 10px 20px rgba(229, 9, 20, 0.15); border-color: #E50914 !important; }
    button[kind="primary"] { background-color: #E50914 !important; color: white !important; border: none !important; border-radius: 8px !important; font-weight: bold !important; font-size: 1.1rem !important; padding: 0.6rem 2rem !important; transition: background-color 0.3s ease; }
    button[kind="primary"]:hover { background-color: #B20710 !important; }
    div[data-testid="stInfo"] { background-color: rgba(229, 9, 20, 0.05); border-left: 4px solid #E50914; color: #FAFAFA; }
</style>
""", unsafe_allow_html=True)

INTERNAL_CTYPES = ["movie", "tv", "documentary", "animation", "anime", "short"]
INTERNAL_ORIGINS = ["all", "local", "international"]
INTERNAL_GENRES = ["comedy", "scifi", "drama", "arthouse", "thriller", "festival"]

LANG_DICT = {
    "US": {"sub": "Discover content tailored to your region.", "prof": "👤 Profile & Limits", "plat": "Subscriptions", "dir": "Director (Optional)", "kw": "Keywords", "bound": "Boundaries", "mem": "🧠 Taste Memory", "like": "Liked", "dis": "Disliked", "hist": "📋 Watch History", "no_hist": "No history.", "mood_title": "🍿 What's your mood today?", "mood_default": "Looking for something relaxing and intriguing.", "btn": "Suggest Content", "warn": "Select at least 1 platform.", "spin": "Analyzing catalogs...", "ai_eval": "🤖 AI Evaluation", "no_match": "⚠️ No exact match.", "recs": "🎬 Catalog Hits", "p_info": "Platform:", "w": "👁️ Watched", "l": "👍 Like", "d": "👎 Dislike", "ctype_lbl": "Content Type", "ctypes": ["Movie", "TV Series", "Documentary", "Animation", "Anime", "Short Film"], "origin_lbl": "Production Origin", "origins": ["All Productions", "Local / Domestic", "International Only"], "genres_lbl": "Genres", "genres": ["Comedy", "Sci-Fi", "Drama", "Arthouse", "Thriller", "Festival Content"]},
    "GB": {"sub": "Discover content tailored to your region.", "prof": "👤 Profile & Limits", "plat": "Subscriptions", "dir": "Director", "kw": "Keywords", "bound": "Boundaries", "mem": "🧠 Taste Memory", "like": "Liked", "dis": "Disliked", "hist": "📋 Watch History", "no_hist": "No history.", "mood_title": "🍿 What's your mood today?", "mood_default": "Looking for something thought-provoking.", "btn": "Suggest Content", "warn": "Select at least 1 platform.", "spin": "Analyzing catalogues...", "ai_eval": "🤖 AI Evaluation", "no_match": "⚠️ No exact match.", "recs": "🎬 Catalogue Hits", "p_info": "Platform:", "w": "👁️ Watched", "l": "👍 Like", "d": "👎 Dislike", "ctype_lbl": "Content Type", "ctypes": ["Movie", "TV Series", "Documentary", "Animation", "Anime", "Short Film"], "origin_lbl": "Production Origin", "origins": ["All Productions", "British / Local", "International Only"], "genres_lbl": "Genres", "genres": ["Comedy", "Sci-Fi", "Drama", "Arthouse", "Thriller", "Festival Content"]},
    "TR": {"sub": "Bulunduğunuz bölgeye ve platformlarınıza uygun içeriği keşfedin.", "prof": "👤 Profil ve Sınırlar", "plat": "Platformlarınız", "dir": "Yönetmen (Opsiyonel)", "kw": "Özel Temalar", "bound": "Kesin Sınırlar", "mem": "🧠 AI Zevk Hafızası", "like": "Beğenilen", "dis": "Beğenilmeyen", "hist": "📋 İzleme Geçmişi", "no_hist": "Henüz içerik yok.", "mood_title": "🍿 Bugün ne izlemek istiyorsunuz?", "mood_default": "Kafamı dağıtacak, merak uyandırıcı bir şeyler arıyorum.", "btn": "İçerik Öner", "warn": "En az 1 platform seçin.", "spin": "Kataloglar inceleniyor...", "ai_eval": "🤖 AI Değerlendirmesi", "no_match": "⚠️ Bu bölgede uyan içerik bulunamadı.", "recs": "🎬 Seçilen İçerikler", "p_info": "Platform:", "w": "👁️ İzledim", "l": "👍 Beğendim", "d": "👎 Beğenmedim", "ctype_lbl": "İçerik Türü", "ctypes": ["Sinema Filmi", "Dizi", "Belgesel", "Animasyon / Çizgi Film", "Anime", "Kısa Film"], "origin_lbl": "Yapım Menşei", "origins": ["Tümü (Yerli & Yabancı)", "Sadece Yerli Yapımlar 🇹🇷", "Sadece Uluslararası Yapımlar 🌍"], "genres_lbl": "Sevdiğiniz Türler", "genres": ["Komedi", "Bilim Kurgu", "Dram", "Arthouse", "Gerilim", "Festival İçerikleri"]},
    "DE": {"sub": "Entdecken Sie Inhalte für Ihre Region.", "prof": "👤 Profil", "plat": "Abonnements", "dir": "Regisseur", "kw": "Schlüsselwörter", "bound": "Grenzen", "mem": "🧠 KI-Geschmack", "like": "Gefällt mir", "dis": "Gefällt nicht", "hist": "📋 Verlauf", "no_hist": "Kein Verlauf.", "mood_title": "🍿 Was möchten Sie heute sehen?", "mood_default": "Ich suche etwas Entspannendes.", "btn": "Inhalte vorschlagen", "warn": "Plattform wählen.", "spin": "KI analysiert...", "ai_eval": "🤖 KI-Berater", "no_match": "⚠️ Keine Übereinstimmung.", "recs": "🎬 Inhalte", "p_info": "Plattform:", "w": "👁️ Gesehen", "l": "👍 Mag ich", "d": "👎 Mag nicht", "ctype_lbl": "Inhaltstyp", "ctypes": ["Film", "Serie", "Dokumentation", "Animation", "Anime", "Kurzfilm"], "origin_lbl": "Produktionsherkunft", "origins": ["Alle Produktionen", "Deutsche / Lokale Produktionen", "Nur Internationale Produktionen"], "genres_lbl": "Genres", "genres": ["Komödie", "Sci-Fi", "Drama", "Arthouse", "Thriller", "Festival-Inhalte"]},
    "ES": {"sub": "Descubre contenido para tu región.", "prof": "👤 Perfil", "plat": "Suscripciones", "dir": "Director", "kw": "Palabras Clave", "bound": "Límites", "mem": "🧠 Memoria IA", "like": "Me gusta", "dis": "No me gusta", "hist": "📋 Historial", "no_hist": "Sin historial.", "mood_title": "🍿 ¿Qué quieres ver hoy?", "mood_default": "Busco algo relajante.", "btn": "Sugerir", "warn": "Selecciona plataforma.", "spin": "Analizando...", "ai_eval": "🤖 Evaluación IA", "no_match": "⚠️ Sin coincidencias.", "recs": "🎬 Contenido", "p_info": "Plataforma:", "w": "👁️ Visto", "l": "👍 Me gusta", "d": "👎 No me gusta", "ctype_lbl": "Tipo de contenido", "ctypes": ["Película", "Serie", "Documental", "Animación", "Anime", "Cortometraje"], "origin_lbl": "Origen de Producción", "origins": ["Todas las Producciones", "Producciones Nacionales", "Solo Internacionales"], "genres_lbl": "Géneros", "genres": ["Comedia", "Ciencia Ficción", "Drama", "Arthouse", "Suspense", "Festival"]},
    "BR": {"sub": "Descubra conteúdos para sua região.", "prof": "👤 Perfil", "plat": "Assinaturas", "dir": "Diretor", "kw": "Palavras-chave", "bound": "Limites", "mem": "🧠 Memória IA", "like": "Gostei", "dis": "Não Gostei", "hist": "📋 Histórico", "no_hist": "Sem histórico.", "mood_title": "🍿 O que quer ver hoje?", "mood_default": "Procuro algo intrigante.", "btn": "Sugerir Conteúdo", "warn": "Selecione plataforma.", "spin": "Analisando...", "ai_eval": "🤖 Avaliação IA", "no_match": "⚠️ Sem correspondência.", "recs": "🎬 Sugeridos", "p_info": "Plataforma:", "w": "👁️ Assistido", "l": "👍 Gostei", "d": "👎 Não Gostei", "ctype_lbl": "Tipo de Conteúdo", "ctypes": ["Filme", "Série", "Documentário", "Animação", "Anime", "Curta-metragem"], "origin_lbl": "Origem da Produção", "origins": ["Todas as Produções", "Nacionais / Brasileiras", "Apenas Internacionais"], "genres_lbl": "Gêneros", "genres": ["Comédia", "Ficção Científica", "Drama", "Arthouse", "Suspense", "Festival"]},
    "RU": {"sub": "Контент для вашего региона.", "prof": "👤 Профиль", "plat": "Подписки", "dir": "Режиссер", "kw": "Ключевые слова", "bound": "Границы", "mem": "🧠 Память ИИ", "like": "Нравится", "dis": "Не нравится", "hist": "📋 История", "no_hist": "Нет истории.", "mood_title": "🍿 Что хотите посмотреть?", "mood_default": "Ищу что-то расслабляющее.", "btn": "Предложить", "warn": "Выберите платформу.", "spin": "Анализ...", "ai_eval": "🤖 Оценка ИИ", "no_match": "⚠️ Нет совпадений.", "recs": "🎬 Рекомендации", "p_info": "Платформа:", "w": "👁️ Просмотрено", "l": "👍 Нравится", "d": "👎 Не нравится", "ctype_lbl": "Тип контента", "ctypes": ["Фильм", "Сериал", "Документальный", "Анимация", "Аниме", "Короткометражка"], "origin_lbl": "Производство", "origins": ["Все картины", "Отечественное кино", "Только зарубежное кино"], "genres_lbl": "Жанры", "genres": ["Комедия", "Фантастика", "Драма", "Артхаус", "Триллер", "Фестиваль"]},
    "AE": {"sub": "اكتشف المحتوى المخصص لمنطقتك.", "prof": "👤 الملف الشخصي", "plat": "اشتراكاتك", "dir": "المخرج", "kw": "كلمات مفتاحية", "bound": "حدود", "mem": "🧠 ذاكرة", "like": "أعجبني", "dis": "لم يعجبني", "hist": "📋 سجل", "no_hist": "لا يوجد سجل.", "mood_title": "🍿 ماذا تريد أن تشاهد اليوم؟", "mood_default": "أبحث عن شيء للاسترخاء.", "btn": "اقتراح محتوى", "warn": "اختر منصة.", "spin": "يجري التحليل...", "ai_eval": "🤖 تقييم", "no_match": "⚠️ لا يوجد تطابق.", "recs": "🎬 المحتوى", "p_info": "المنصة:", "w": "👁️ تمت المشاهدة", "l": "👍 أعجبني", "d": "👎 لم يعجبني", "ctype_lbl": "نوع المحتوى", "ctypes": ["فيلم", "مسلسل", "وثائقي", "رسوم متحركة", "أنمي", "فيلم قصير"], "origin_lbl": "أصل الإنتاج", "origins": ["كل الأعمال", "الإنتاج المحلي", "الإنتاج الدولي فقط"], "genres_lbl": "الأنواع", "genres": ["كوميديا", "خيال علمي", "دراما", "فني", "إثارة", "مهرجانات"]},
    "CN": {"sub": "发现适合您所在地区的内容。", "prof": "👤 个人资料", "plat": "您的订阅", "dir": "导演", "kw": "关键词", "bound": "边界", "mem": "🧠 AI 记忆", "like": "喜欢", "dis": "不喜欢", "hist": "📋 观看历史", "no_hist": "暂无记录", "mood_title": "🍿 今天想看什么？", "mood_default": "想看一些轻松的内容。", "btn": "推荐内容", "warn": "请选择平台。", "spin": "分析中...", "ai_eval": "🤖 AI 评估", "no_match": "⚠️ 未找到匹配。", "recs": "🎬 推荐内容", "p_info": "平台:", "w": "👁️ 已看", "l": "👍 喜欢", "d": "👎 不喜欢", "ctype_lbl": "内容类型", "ctypes": ["电影", "电视剧", "纪录片", "动画", "动漫", "短片"], "origin_lbl": "制作来源", "origins": ["全部作品", "国产华语影视", "仅限海外/国际作品"], "genres_lbl": "类型", "genres": ["喜剧", "科幻", "剧情", "艺术", "惊悚", "电影节"]},
    "JP": {"sub": "地域のカタログに合わせたコンテンツ。", "prof": "👤 プロフィール", "plat": "サブスクリプション", "dir": "監督", "kw": "キーワード", "bound": "境界", "mem": "🧠 AI の好み", "like": "いいね", "dis": "よくないね", "hist": "📋 視聴履歴", "no_hist": "履歴なし", "mood_title": "🍿 今日は何を見たいですか？", "mood_default": "リラックスできる作品を探しています。", "btn": "提案する", "warn": "プラットフォームを選択。", "spin": "分析中...", "ai_eval": "🤖 AI 評価", "no_match": "⚠️ 一致しません。", "recs": "🎬 コンテンツ", "p_info": "プラットフォーム:", "w": "👁️ 視聴済み", "l": "👍 いいね", "d": "👎 好きじゃない", "ctype_lbl": "コンテンツの種類", "ctypes": ["映画", "ドラマ", "ドキュメンタリー", "アニメーション", "アニメ", "ショートフィルム"], "origin_lbl": "制作地域", "origins": ["すべての作品", "国内制作（邦画・国内ドラマ）", "海外制作（洋画・海外ドラマ）のみ"], "genres_lbl": "ジャンル", "genres": ["コメディ", "SF", "ドラマ", "アートハウス", "スリラー", "フェスティバル"]}
}

REGION_PLATFORMS = {
    "US": ["Netflix", "Amazon Prime Video", "Disney+", "Apple TV+", "Hulu", "Max", "Peacock", "Paramount+", "MUBI", "Crunchyroll"],
    "GB": ["Netflix", "Amazon Prime Video", "Disney+", "Apple TV+", "NOW", "BBC iPlayer", "Channel 4", "MUBI"],
    "TR": ["Netflix", "Amazon Prime Video", "BluTV", "Disney+", "Apple TV+", "MUBI", "Exxen", "puhutv", "Gain", "TOD"],
    "DE": ["Netflix", "Amazon Prime Video", "Disney+", "Apple TV+", "WOW", "Joyn", "RTL+", "MUBI"],
    "ES": ["Netflix", "Amazon Prime Video", "Disney+", "Apple TV+", "Movistar Plus+", "Filmin", "Max", "MUBI"],
    "BR": ["Netflix", "Amazon Prime Video", "Disney+", "Apple TV+", "Globoplay", "Max", "Crunchyroll", "MUBI"],
    "RU": ["Kinopoisk", "Ivi", "Okko", "Wink", "Premier", "Netflix"],
    "AE": ["Netflix", "Amazon Prime Video", "Disney+", "Apple TV+", "OSN+", "Shahid", "STARZPLAY"],
    "CN": ["iQIYI", "Tencent Video", "Youku", "Bilibili"],
    "JP": ["Netflix", "Amazon Prime Video", "Disney+", "Apple TV+", "U-NEXT", "Hulu", "AbemaTV", "dTV", "MUBI"]
}

st.markdown('<div class="title-logo">EntertainmentAI</div>', unsafe_allow_html=True)

regions = {
    "US (United States)": "US", "GB (United Kingdom)": "GB", "TR (Türkiye)": "TR", 
    "DE (Deutschland)": "DE", "ES (España)": "ES", "BR (Brasil)": "BR", 
    "RU (Россия)": "RU", "AE (الإمارات)": "AE", "CN (中国)": "CN", "JP (日本)": "JP"
}

selected_region_label = st.sidebar.selectbox("Globe", list(regions.keys()), index=2) # Default TR
region = regions[selected_region_label]
t = LANG_DICT[region]

st.markdown(f'<div class="subtitle">{t["sub"]}</div>', unsafe_allow_html=True)
st.sidebar.header(t["prof"])

# İÇERİK TÜRÜ
selected_ctype_name = st.sidebar.selectbox(t["ctype_lbl"], t["ctypes"])
internal_ctype = INTERNAL_CTYPES[t["ctypes"].index(selected_ctype_name)]

# YAPIM KÖKENİ FİLTRESİ
selected_origin_name = st.sidebar.selectbox(t["origin_lbl"], t["origins"])
internal_origin = INTERNAL_ORIGINS[t["origins"].index(selected_origin_name)]

available_platforms = REGION_PLATFORMS.get(region, ["Netflix", "Amazon Prime Video"])
subscriptions = st.sidebar.multiselect(t["plat"], available_platforms, default=[available_platforms[0]] if available_platforms else [])

selected_genre_names = st.sidebar.multiselect(t["genres_lbl"], t["genres"], default=[t["genres"][2]]) # Default Drama
internal_genres = [INTERNAL_GENRES[t["genres"].index(g)] for g in selected_genre_names]

director = st.sidebar.text_input(t["dir"])
keywords = st.sidebar.text_input(t["kw"])
boundaries = st.sidebar.text_input(t["bound"])

memory = get_user_memory()
with st.sidebar.expander(t["mem"], expanded=False):
    st.write(f"**{t['like']}:** {len(memory['liked_titles'])}")
    st.write(f"**{t['dis']}:** {len(memory['disliked_titles'])}")

with st.sidebar.expander(t["hist"], expanded=False):
    if memory['watched_titles']:
        for w_title in memory['watched_titles']: st.caption(f"👁️ {w_title}")
    else: st.caption(t["no_hist"])

st.markdown(f"### {t['mood_title']}")
mood = st.text_area("Mood", value=t["mood_default"], key=f"mood_input_{region}", label_visibility="collapsed")

if "recommendations" not in st.session_state: st.session_state.recommendations = None
if "ai_comment" not in st.session_state: st.session_state.ai_comment = None
if "no_match_found" not in st.session_state: st.session_state.no_match_found = False

if st.button(t["btn"], type="primary"):
    if not subscriptions:
        st.warning(t["warn"])
    else:
        with st.spinner(t["spin"]):
            user_profile = {
                "region": region,
                "content_type": internal_ctype,
                "origin": internal_origin,
                "genres": internal_genres,
                "subscriptions": subscriptions,
                "boundaries": boundaries,
                "keywords": keywords,
                "director": director,
                "mood": mood
            }
            try:
                raw_candidates = search_content(user_profile)
                watched_ids = memory["watched_ids"]
                filtered_candidates = [m for m in raw_candidates if m["id"] not in watched_ids] if raw_candidates else []
                
                unique_candidates = []
                seen_titles = set()
                for c in filtered_candidates:
                    norm_title = c["title"].strip().lower()
                    if norm_title not in seen_titles:
                        seen_titles.add(norm_title); unique_candidates.append(c)

                no_match = bool(keywords and not unique_candidates)
                ai_response = generate_recommendation(user_profile, unique_candidates, memory=memory, no_match=no_match)
                
                st.session_state.recommendations = unique_candidates
                st.session_state.ai_comment = ai_response
                st.session_state.no_match_found = no_match
            except Exception as e:
                st.error(f"Error: {e}")

if st.session_state.ai_comment:
    st.markdown("---")
    st.markdown(f"### {t['ai_eval']}")
    st.info(st.session_state.ai_comment)

    if st.session_state.no_match_found:
        st.warning(t["no_match"])
    elif st.session_state.recommendations:
        st.markdown(f"<br><h3>{t['recs']}</h3>", unsafe_allow_html=True)
        cols = st.columns(2)
        
        for idx, item in enumerate(st.session_state.recommendations[:4]):
            col = cols[idx % 2]
            with col:
                with st.container(border=True):
                    c_img, c_info = st.columns([1, 2.2])
                    with c_img:
                        poster_url = f"https://image.tmdb.org/t/p/w500{item.get('poster_path')}" if item.get("poster_path") else "https://via.placeholder.com/500x750?text=No+Poster"
                        st.image(poster_url, use_container_width=True)
                    
                    with c_info:
                        st.markdown(f"#### {item.get('title')}")
                        st.markdown(f"📅 **{str(item.get('release_date', ''))[:4]}** &nbsp;|&nbsp; ⭐ **{item.get('vote_average', 0):.1f}/10**")
                        p_badges = " ".join([f"`{p}`" for p in item.get("matched_platforms", [])])
                        st.markdown(f"📺 **{t['p_info']}** {p_badges if p_badges else 'N/A'}")
                        st.markdown(f"<div style='font-size:0.9rem; color:#A0AAB2; margin-top:10px;'>{item.get('overview')[:130]}...</div>", unsafe_allow_html=True)
                    
                    st.markdown("<br>", unsafe_allow_html=True)
                    b1, b2, b3 = st.columns(3)
                    i_id, i_title = item["id"], item["title"]
                    with b1:
                        if st.button(t["w"], key=f"w_{i_id}", use_container_width=True): record_feedback(i_id, i_title, "watched"); st.rerun()
                    with b2:
                        if st.button(t["l"], key=f"l_{i_id}", use_container_width=True): record_feedback(i_id, i_title, "liked"); st.rerun()
                    with b3:
                        if st.button(t["d"], key=f"d_{i_id}", use_container_width=True): record_feedback(i_id, i_title, "disliked"); st.rerun()