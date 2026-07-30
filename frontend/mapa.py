import pyproj
import streamlit as st
import folium
from streamlit_folium import st_folium
from shapely.geometry import Point
from shapely.ops import transform

import sys
from pathlib import Path

# Adiciona a pasta raiz do projeto (um nível acima do arquivo atual) ao caminho do Python
RAIZ_PROJETO = Path(__file__).resolve().parent.parent
if str(RAIZ_PROJETO) not in sys.path:
    sys.path.append(str(RAIZ_PROJETO))

# Agora os imports funcionam normalmente:
from processamento.carregar_dados import carregar_todos
from processamento.distancias import calcular_distancias, filtrar_por_raio
from processamento.geometrias import converter_multipoint
from processamento.pontuacao import (
    calcular_pontuacao,
    calcular_todos_os_perfis,
    pontuacao_total,
)



# 1. Carregamento dos dados com Cache para evitar releitura constante do disco
@st.cache_data
def carregar_dados_cache():
    return carregar_todos()


# 2. Conversão da coordenada Lat/Lon (WGS84) para UTM (Métrica)
def converter_latlon_para_utm(lat: float, lon: float) -> Point:
    ponto_wgs84 = Point(lon, lat)
    # Define a transformação do WGS84 (EPSG:4326) para SIRGAS 2000 / UTM zone 23S (EPSG:31983)
    transformer = pyproj.Transformer.from_crs(
        "EPSG:4326", "EPSG:31983", always_xy=True
    )
    ponto_utm = transform(transformer.transform, ponto_wgs84)
    return ponto_utm


def render_mapa():
    st.set_page_config(page_title="UrbanChoice", layout="wide")

    st.title("🌍 UrbanChoice")
    st.write("Selecione um ponto do mapa de Santo André a ser analisado.")

    # Inicialização do Session State
    if "lat" not in st.session_state:
        st.session_state.lat = -23.644912
    if "lon" not in st.session_state:
        st.session_state.lon = -46.527910
    if "ponto_selecionado" not in st.session_state:
        st.session_state.ponto_selecionado = (
            st.session_state.lat,
            st.session_state.lon,
        )
    if "raio_analise" not in st.session_state:
        st.session_state.raio_analise = 3000

    # Barra lateral
    st.sidebar.header("Configurações")
    st.session_state.raio_analise = st.sidebar.slider(
        "Raio de análise (metros)",
        min_value=500,
        max_value=5000,
        value=st.session_state.raio_analise,
        step=100,
    )

    # Construção do Mapa
    mapa = folium.Map(
        location=[st.session_state.lat, st.session_state.lon], zoom_start=13
    )

    folium.Marker(
        [st.session_state.lat, st.session_state.lon], tooltip="Ponto selecionado"
    ).add_to(mapa)

    folium.Circle(
        location=[st.session_state.lat, st.session_state.lon],
        radius=st.session_state.raio_analise,
        color="red",
        fill=True,
        fill_opacity=0.2,
    ).add_to(mapa)

    dados_mapa = st_folium(mapa, width=900, height=600)

    # Captura clique no mapa
    if dados_mapa and dados_mapa.get("last_clicked"):
        nova_lat = dados_mapa["last_clicked"]["lat"]
        nova_lon = dados_mapa["last_clicked"]["lng"]

        if nova_lat != st.session_state.lat or nova_lon != st.session_state.lon:
            st.session_state.lat = nova_lat
            st.session_state.lon = nova_lon
            st.session_state.ponto_selecionado = (nova_lat, nova_lon)
            st.rerun()

    # Exibição das Coordenadas
    st.subheader("Ponto selecionado")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Latitude", f"{st.session_state.lat:.6f}")
    with col2:
        st.metric("Longitude", f"{st.session_state.lon:.6f}")

    # Processamento do Backend ao Clicar
    if st.button("Analisar área"):
        with st.spinner("Carregando camadas e calculando pontuações..."):
            # A. Converte coordenadas
            ponto_utm = converter_latlon_para_utm(
                st.session_state.lat, st.session_state.lon
            )

            # B. Obtém dados do GeoPackage
            dados = carregar_dados_cache()
            raio = st.session_state.raio_analise
            pontuacoes_por_camada = {}

            # C. Executa o pipeline para cada camada
            for nome, gdf in dados.items():
                gdf = converter_multipoint(gdf)
                gdf = calcular_distancias(gdf, ponto_utm)
                gdf = filtrar_por_raio(gdf, raio)
                gdf = calcular_pontuacao(gdf)

                p_total = pontuacao_total(gdf)
                pontuacoes_por_camada[nome] = p_total

            # D. Calcula perfis
            perfis_pontuacao = calcular_todos_os_perfis(pontuacoes_por_camada)

        st.success("Análise concluída!")

        # E. Exibe os Resultados no Frontend
        st.subheader("📊 Pontuação por Perfil")
        cols = st.columns(len(perfis_pontuacao))

        for idx, (perfil, pontuacao) in enumerate(perfis_pontuacao.items()):
            with cols[idx]:
                st.metric(
                    label=f"Perfil: {perfil.capitalize()}",
                    value=f"{(pontuacao*(100/1300)):.2f} pontos",
                )

        # Detalhamento por Camada
        with st.expander("Ver detalhamento das pontuações por camada"):
            st.json(pontuacoes_por_camada)


if __name__ == "__main__":
    render_mapa()