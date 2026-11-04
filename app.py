import streamlit as st
from tmdb_api import search_content, get_streaming_platforms
from ai_agent import generate_recommendation
from database import init_db, add_feedback

init_db()

st.set_page_config(page_title="EntertainmentAI", page_icon="🎬", layout="wide")
st.title("EntertainmentAI 🎬")
st.markdown("Zaman kaybetmeden ruh halinize ve platformlarınıza uygun içeriği bulun.")

st.sidebar.header("👤 Profil ve Sınırlar")
region = st.sidebar.selectbox("Bulunduğunuz Ülke", ["TR", "US", "DE", "GB"])
subscriptions = st.sidebar.multiselect(
    "Sahip Olduğunuz Platformlar", 
    ["Netflix", "Amazon Prime Video", "BluTV", "Disney+", "Apple TV+"],
    default=["Netflix"]
)
genres = st.sidebar.multiselect(
    "Sevdiğiniz Türler", 
    ["Komedisi", "Bilim Kurgu", "Dram", "Arthouse", "Belgesel", "Gerilim"],
    default=["Komedisi", "Bilim Kurgu"]
)
boundaries = st.sidebar.text_input("Kesin Sınırlarınız (İstemediğiniz şeyler)", "Aşırı şiddet, jump-scare")

st.subheader("Bugün ne izlemek istiyorsunuz?")
mood = st.text_area("Ruh halinizi anlatın:", "Çok yorgunum, kafamı dağıtacak çerezlik bir şeyler arıyorum.")

if st.button("Bana İçerik Öner"):
    if not subscriptions or not genres:
        st.warning("Lütfen yan menüden en az bir platform ve tür seçin.")
    else:
        with st.spinner("Yapay zeka asistanınız içerikleri inceliyor..."):
            user_profile = {
                "region": region,
                "genres": genres,
                "subscriptions": subscriptions,
                "boundaries": boundaries,
                "mood": mood
            }

            arama_sonucu = search_content(genres[0]) 
            
            tmdb_data = []
            if arama_sonucu:
                platformlar = get_streaming_platforms(arama_sonucu['id'], region=region)
                tmdb_data.append({
                    "title": arama_sonucu.get('title', arama_sonucu.get('name', 'Bilinmiyor')),
                    "platforms": platformlar,
                    "genre": genres[0],
                    "overview": arama_sonucu.get('overview', '')
                })
            else:
                st.error("Kriterlere uygun popüler içerik çekilemedi.")

            if tmdb_data:
                ai_response = generate_recommendation(user_profile, tmdb_data)
                
                st.success("İşte sizin için seçtiklerim!")
                st.write(ai_response)

                st.markdown("---")
                st.write("Bu öneriyi nasıl buldunuz?")
                col1, col2, col3 = st.columns(3)
                
                onerilen_film = tmdb_data[0]['title']
                
                if col1.button("👍 Tam Aradığım Gibi"):
                    add_feedback(onerilen_film, "Beğenildi", "Olumlu")
                    st.toast("Geri bildiriminiz kaydedildi!")
                if col2.button("👎 Sınırlarımı İhlal Etti"):
                    add_feedback(onerilen_film, "Sınır İhlali", "Olumsuz")
                    st.toast("Profilinizi güncellemek için kaydedildi.")
                if col3.button("🤷‍♂️ Platform Uymadı"):
                    add_feedback(onerilen_film, "Platform Hatası", "Olumsuz")
                    st.toast("Platform tercihlerinize daha çok dikkat edeceğim.")