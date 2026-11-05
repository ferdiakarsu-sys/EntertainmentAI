from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
import re

LANGUAGE_CONFIGS = {
    "TR": {
        "name": "Turkish", "native": "Türkçe", "greeting": "Merhaba!",
        "directive": "Sen profesyonel bir film ve dizi danışmanısın. Cevabının TAMAMINI İSTİSNASIZ TÜRKÇE yazacaksın. Asla tek bir İngilizce cümle veya kelime kullanma."
    },
    "US": {
        "name": "English", "native": "English", "greeting": "Hello!",
        "directive": "You are a movie and TV recommender. Write your ENTIRE response strictly and naturally in English."
    },
    "GB": {
        "name": "British English", "native": "English", "greeting": "Hello!",
        "directive": "You are a movie and TV recommender. Write your ENTIRE response strictly and naturally in British English."
    },
    "DE": {
        "name": "German", "native": "Deutsch", "greeting": "Hallo!",
        "directive": "Du bist ein professioneller Film- und Serienberater. Du MUSST deine gesamte Antwort ausnahmslos auf DEUTSCH verfassen. Kein einziges Wort auf Englisch oder Türkisch!"
    },
    "ES": {
        "name": "Spanish", "native": "Español", "greeting": "¡Hola!",
        "directive": "Eres un asesor de cine y series. Debes redactar TODA tu respuesta obligatoriamente en ESPAÑOL. Está estrictamente prohibido usar inglés o turco."
    },
    "BR": {
        "name": "Portuguese", "native": "Português", "greeting": "Olá!",
        "directive": "Você é um consultor profissional de filmes e séries. Escreva TODA a sua resposta estritamente em PORTUGUÊS. Não use inglês em nenhuma hipótese."
    },
    "RU": {
        "name": "Russian", "native": "Русский", "greeting": "Здравствуйте!",
        "directive": "Вы профессиональный консультант по кино. Вы ДОЛЖНЫ написать весь свой ответ исключительно на РУССКОМ языке. Никакого английского языка."
    },
    "AE": {
        "name": "Arabic", "native": "العربية", "greeting": "مرحباً!",
        "directive": "أنت مستشار سينمائي محترف. يجب أن تكتب ردك كاملاً باللغة العربية الفصحى فقط وبشكل صارم. يُمنع منعاً باتاً استخدام اللغة الإنجليزية."
    },
    "CN": {
        "name": "Simplified Chinese", "native": "简体中文", "greeting": "你好！",
        "directive": "你是一位专业的电影与电视剧推荐顾问。你的所有内容必须【100%全中文】输出。绝对严禁输出任何英语句子！"
    },
    "JP": {
        "name": "Japanese", "native": "日本語", "greeting": "こんにちは！",
        "directive": "あなたは映画・ドラマのレコメンド専門AIです。回答は最初から最後まで完全に自然な日本語のみで記述してください。英語の混入は厳禁です。"
    }
}

ENGLISH_PATTERNS = [
    r"\bbased on\b", r"\brecommend(ation|ations|ed)?\b", r"\bcurated\b", 
    r"\bexciting\b", r"\bfit your\b", r"\bavailable on\b", r"\boriginal series\b",
    r"\bgreat match\b", r"\bwill resonate\b", r"\bkeep you entertained\b",
    r"\bi hope you\b", r"\bthese titles\b", r"\bmovie(s)?\b", r"\bshow(s)?\b"
]

def verify_and_enforce_language(text, region, llm):
    """
    Hedef dil dışındaki sızıntıları yakalayan ve düzelten güvenlik duvarı.
    """
    cfg = LANGUAGE_CONFIGS.get(region, LANGUAGE_CONFIGS["US"])
    needs_translation = False

    # 1. İngilizce olmayan tüm dillerde (TR, DE, ES, CN vb.) İngilizce sızıntı kontrolü
    if region not in ["US", "GB"]:
        text_lower = text.lower()
        matches = sum(1 for pat in ENGLISH_PATTERNS if re.search(pat, text_lower))
        if matches >= 2:
            needs_translation = True

    # 2. Alfabe kontrolü (Çince, Japonca, Arapça, Rusça için)
    if region in ["CN", "JP"] and not bool(re.search(r'[\u4e00-\u9fff\u3040-\u30ff]', text)):
        needs_translation = True
    elif region == "AE" and not bool(re.search(r'[\u0600-\u06FF]', text)):
        needs_translation = True
    elif region == "RU" and not bool(re.search(r'[\u0400-\u04FF]', text)):
        needs_translation = True

    # Sapma varsa doğrudan o dile zorunlu çeviri uygula
    if needs_translation:
        fix_prompt = (
            f"Translate the following text strictly into natural, fluent {cfg['native']} ({cfg['name']}). "
            f"Keep title names and platform tags intact. Do NOT include any English sentences. "
            f"Output ONLY the translated text in {cfg['native']}:\n\n{text}"
        )
        try:
            translated = llm.invoke(fix_prompt).content.strip()
            return translated
        except Exception:
            return text
            
    return text

def generate_recommendation(user_profile, tmdb_data, memory=None, no_match=False, **kwargs):
    llm = ChatOllama(model="llama3", temperature=0.2)
    region = user_profile.get("region", "TR")
    cfg = LANGUAGE_CONFIGS.get(region, LANGUAGE_CONFIGS["TR"])

    memory = memory or {}
    watched_str = ", ".join(memory.get("watched_titles", [])) or "None"

    if no_match or not tmdb_data:
        movies_text = f"Inform the user in {cfg['native']} that their search criteria returned no matches on their platforms. Suggest rich alternative themes."
    else:
        movie_items = []
        for idx, m in enumerate(tmdb_data[:4], 1):
            t = m.get("title", "Unknown")
            y = str(m.get("release_date", ""))[:4]
            user_plats = ", ".join(m.get("matched_platforms", [])) or "Platform"
            o = m.get("overview", "")[:200]
            movie_items.append(f"{idx}. {t} ({y}) | Platform: {user_plats}\nÖzet: {o}")
        movies_text = "İçerik Havuzu:\n" + "\n\n".join(movie_items)

    system_message = (
        f"{cfg['directive']}\n"
        f"ZORUNLU BAŞLANGIÇ: Yanıtına doğrudan '{cfg['greeting']}' diyerek başla.\n"
        f"KATI KURAL: Tüm değerlendirmeni ve öneri gerekçelerini YALNIZCA {cfg['native']} dilinde yaz. İngilizce tek bir açıklama dahi yapma."
    )

    human_message = f"""Kullanıcı Profili:
- Hedef Çıktı Dili: {cfg['native']}
- Format: {user_profile.get('content_type', 'movie')}
- Yapım Tercihi: {user_profile.get('origin', 'all')}
- Ruh Hali: {user_profile.get('mood')}
- Platformlar: {', '.join(user_profile.get('subscriptions', []))}
- Özel Temalar: {user_profile.get('keywords') or 'Yok'}
- Daha Önce İzlenenler (Önerme): {watched_str}

{movies_text}

Değerlendirmeni ve her içeriğin neden uygun olduğunu açıkla.
METNİN TAMAMI KESİNLİKLE {cfg['native']} DİLİNDE OLMALIDIR."""

    prompt = ChatPromptTemplate.from_messages([("system", system_message), ("human", human_message)])
    raw_response = (prompt | llm).invoke({}).content
    return verify_and_enforce_language(raw_response, region, llm)