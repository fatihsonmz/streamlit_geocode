import streamlit as st
import pandas as pd
import io
import folium
from streamlit_folium import folium_static
from geopy.geocoders import Photon
import time
import json  # GeoJSON verisi için

st.title("Adres Coğrafi Kodlama ve Harita Görselleştirme - Geocode")

# Excel dosyasını yüklemek için alan
uploaded_file = st.file_uploader("Excel dosyasını yükleyin", type=["xlsx", "xls"])

# Adresleri coğrafi koda çevirmek için Photon kullanımı
def geocode_address_photon(address, retry_count=3):
    geolocator = Photon(user_agent="my-photon-geocoder", timeout=10)  # Photon kullanımı
    try:
        location = geolocator.geocode(address)
        if location:
            return (location.latitude, location.longitude)
        else:
            return (None, None)
    except Exception as e:
        if retry_count > 0:
            time.sleep(1)
            return geocode_address_photon(address, retry_count - 1)
        else:
            st.warning(f"Photon servisi hatası: {e}")
            return (None, None)

# Excel dosyasını işle
if uploaded_file is not None:
    try:
        # Excel dosyasını byte akışına çevir
        data = uploaded_file.getvalue()
        # Excel verilerini DataFrame olarak oku
        df = pd.read_excel(io.BytesIO(data))

        # Kullanıcıdan adres sütununu seçmesini iste
        address_column = st.selectbox("Adres sütununu seçin", df.columns)

        if address_column:
            # Adresleri coğrafi koda çevir
            geocoded_data = []
            st.write("Coğrafi kodlama işlemi başlatılıyor...")

            for address in df[address_column]:
                if pd.isna(address):
                    st.warning(f"Boş adres atlandı: {address}")
                    continue

                # Photon ile coğrafi kodlama işlemi
                st.write(f"İşleniyor: {address}")
                latitude, longitude = geocode_address_photon(address)

                if latitude is not None and longitude is not None:
                    geocoded_data.append([address, latitude, longitude])
                else:
                    st.warning(f"Adres coğrafi koda çevrilemedi: {address}")

            if geocoded_data:
                # Yeni bir DataFrame oluştur
                geocoded_df = pd.DataFrame(geocoded_data, columns=["Adres", "Enlem", "Boylam"])

                # Coğrafi kodlanmış veriyi göster
                st.subheader("Coğrafi Kodlanmış Veriler")
                st.dataframe(geocoded_df)

                # CSV İndirme seçeneği ekle
                st.subheader("Coğrafi Kodlanmış Veriyi İndirin")
                csv = geocoded_df.to_csv(index=False)
                st.download_button(
                    label="CSV Olarak İndir",
                    data=csv,
                    file_name="coğrafi_kodlanmış_veri.csv",
                    mime="text/csv",
                )

                # GeoJSON formatını oluştur
                geojson_features = []
                for _, row in geocoded_df.iterrows():
                    feature = {
                        "type": "Feature",
                        "geometry": {
                            "type": "Point",
                            "coordinates": [row["Boylam"], row["Enlem"]],
                        },
                        "properties": {
                            "address": row["Adres"]
                        }
                    }
                    geojson_features.append(feature)

                geojson_data = {
                    "type": "FeatureCollection",
                    "features": geojson_features
                }

                # GeoJSON dosyasını string olarak kaydet
                geojson_str = json.dumps(geojson_data, ensure_ascii=False)

                # GeoJSON indirme seçeneği ekle
                st.download_button(
                    label="GeoJSON Olarak İndir",
                    data=geojson_str,
                    file_name="coğrafi_kodlanmış_veri.geojson",
                    mime="application/geo+json",
                )

                # Harita oluştur
                m = folium.Map(location=[geocoded_df["Enlem"].mean(), geocoded_df["Boylam"].mean()], zoom_start=10)

                # Haritaya işaretler ekle
                for _, row in geocoded_df.iterrows():
                    folium.Marker([row["Enlem"], row["Boylam"]], popup=row["Adres"]).add_to(m)

                # Haritayı göster
                st.subheader("Harita Görselleştirmesi")
                folium_static(m)
            else:
                st.error("Hiçbir adres coğrafi kodlanamadı. Lütfen sütun adını ve Excel dosyasındaki verileri kontrol edin.")
    except Exception as e:
        st.error(f"Excel dosyası okunurken hata oluştu: {e}")
