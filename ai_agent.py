import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate

# .env dosyasındaki ortam değişkenlerini yükler
load_dotenv()

def generate_recommendation(user_profile, tmdb_data):
    # Anlık 503 yoğunluk hatalarına karşı max_retries tanımlı güncel Gemini modeli
    llm = ChatGoogleGenerativeAI(
        model="gemini-3.8-flash",
        temperature=0.7,
        max_retries=4
    )

    prompt_template = PromptTemplate(
        input_variables=["region", "genres", "subscriptions", "boundaries", "mood", "movies"],
        template="""
Sen profesyonel bir içerik önerme asistanısın. Görevin, kullanıcının profiline ve sınırlarına tamamen saygı duyarak, aşağıdaki listeden en uygun içerikleri seçmek ve samimi bir dille önermektir.

Kullanıcı Profili:
- Ülke: {region}
- Sevdiği Türler: {genres}
- Sahip Olduğu Platformlar: {subscriptions}
- Kesin Sınırları (İstemediği şeyler): {boundaries}
- Ruh Hali: {mood}

TMDB'den Gelen Potansiyel İçerikler ve Platformları:
{movies}

Kurallar:
1. Sadece kullanıcının sahip olduğu platformlardaki içerikleri öner.
2. Kullanıcının sınırlarını ihlal etme potansiyeli olan hiçbir içeriği önerme.
3. Seçtiğin içerikleri neden seçtiğini, ruh haline nasıl uyduğunu ve hangi platformda olduğunu belirterek açıkla.
4. Net ve akıcı bir dil kullan.

Tavsiyen:
"""
    )

    chain = prompt_template | llm
    
    response = chain.invoke({
        "region": str(user_profile.get('region', '')),
        "genres": ", ".join(user_profile.get('genres', [])) if isinstance(user_profile.get('genres'), list) else str(user_profile.get('genres', '')),
        "subscriptions": ", ".join(user_profile.get('subscriptions', [])) if isinstance(user_profile.get('subscriptions'), list) else str(user_profile.get('subscriptions', '')),
        "boundaries": str(user_profile.get('boundaries', '')),
        "mood": str(user_profile.get('mood', '')),
        "movies": str(tmdb_data)
    })
    
    return response.content