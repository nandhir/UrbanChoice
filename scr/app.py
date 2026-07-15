import streamlit as st
import folium
from streamlit_folium import st_folium

# Configuração da página
st.set_page_config(
    page_title="UrbanChoice",
    layout="wide"
)

st.title("🌍 UrbanChoice")
st.write("Clique em qualquer ponto do mapa para selecionar uma área de análise.")

# Inicializa o Session State
if "lat" not in st.session_state:
    st.session_state.lat = -23.644912

if "lon" not in st.session_state:
    st.session_state.lon = -46.527910

# Barra lateral
st.sidebar.header("Configurações")

raio = st.sidebar.slider(
    "Raio de análise (metros)",
    min_value=500,
    max_value=10000,
    value=3000,
    step=500
)

# Cria o mapa
mapa = folium.Map(
    location=[st.session_state.lat, st.session_state.lon],
    zoom_start=13
)

# Marcador
folium.Marker(
    [st.session_state.lat, st.session_state.lon],
    tooltip="Ponto selecionado"
).add_to(mapa)

# Círculo de análise
folium.Circle(
    location=[st.session_state.lat, st.session_state.lon],
    radius=raio,
    color="red",
    fill=True,
    fill_opacity=0.2
).add_to(mapa)

# Exibe o mapa
dados_mapa = st_folium(
    mapa,
    width=900,
    height=600
)

# Captura o clique
if dados_mapa["last_clicked"] is not None:

    st.session_state.lat = dados_mapa["last_clicked"]["lat"]
    st.session_state.lon = dados_mapa["last_clicked"]["lng"]

    st.rerun()

# Informações
st.subheader("Ponto selecionado")

col1, col2 = st.columns(2)

with col1:
    st.metric("Latitude", f"{st.session_state.lat:.6f}")

with col2:
    st.metric("Longitude", f"{st.session_state.lon:.6f}")

# Botão de análise
if st.button("Analisar área"):

    st.success("Análise iniciada!")

    st.write("Latitude:", st.session_state.lat)
    st.write("Longitude:", st.session_state.lon)
    st.write("Raio:", raio, "metros")

    # Aqui futuramente você chamará suas funções
    # resultado = analisar_area(
    #     st.session_state.lat,
    #     st.session_state.lon,
    #     raio
    # )