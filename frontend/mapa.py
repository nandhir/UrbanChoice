import sys
from pathlib import Path

# Adiciona a pasta raiz do projeto ao caminho do Python
RAIZ_PROJETO = Path(__file__).resolve().parent.parent
if str(RAIZ_PROJETO) not in sys.path:
    sys.path.append(str(RAIZ_PROJETO))

import pyproj
import streamlit as st
import folium
from streamlit_folium import st_folium
from shapely.geometry import Point
from shapely.ops import transform

from processamento.carregar_dados import carregar_todos
from processamento.distancias import calcular_distancias, filtrar_por_raio
from processamento.geometrias import converter_multipoint
from processamento.pontuacao import (
    PERFIS,
    calcular_pontuacao,
    calcular_todos_os_perfis,
    pontuacao_total,
)


@st.cache_data
def carregar_dados_cache():
    return carregar_todos()


def converter_latlon_para_utm(lat: float, lon: float) -> Point:
    ponto_wgs84 = Point(lon, lat)
    transformer = pyproj.Transformer.from_crs(
        "EPSG:4326", "EPSG:31983", always_xy=True
    )
    return transform(transformer.transform, ponto_wgs84)


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

    dados = carregar_dados_cache()
    camadas_disponiveis = list(dados.keys())

    # Barra lateral
    st.sidebar.header("Área de Análise")
    st.session_state.raio_analise = st.sidebar.slider(
        "Raio de análise (metros)",
        min_value=500,
        max_value=5000,
        value=st.session_state.raio_analise,
        step=100,
    )
    st.sidebar.write(
        "Para a análise de perfis, o valor padrão de :red[3000 metros] é recomendado."
    )

    # Pesos do Perfil Personalizado na Sidebar
    st.sidebar.subheader("Perfil Personalizado")
    pesos_personalizados = {}
    for camada in camadas_disponiveis:
        valor_padrao = PERFIS["personalizado"].get(camada, 0.10)
        pesos_personalizados[camada] = st.sidebar.number_input(
            f"{camada}",
            min_value=0.0,
            max_value=1.0,
            value=float(valor_padrao),
            step=0.05,
            format="%.3f",
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

    if dados_mapa and dados_mapa.get("last_clicked"):
        nova_lat = dados_mapa["last_clicked"]["lat"]
        nova_lon = dados_mapa["last_clicked"]["lng"]

        if nova_lat != st.session_state.lat or nova_lon != st.session_state.lon:
            st.session_state.lat = nova_lat
            st.session_state.lon = nova_lon
            st.session_state.ponto_selecionado = (nova_lat, nova_lon)
            st.rerun()

    st.subheader("Ponto selecionado")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Latitude", f"{st.session_state.lat:.6f}")
    with col2:
        st.metric("Longitude", f"{st.session_state.lon:.6f}")

    if st.button("Analisar área", type="primary"):
        with st.spinner("Carregando camadas e calculando pontuações..."):
            ponto_utm = converter_latlon_para_utm(
                st.session_state.lat, st.session_state.lon
            )
            raio = st.session_state.raio_analise
            pontuacoes_por_camada = {}

            for nome, gdf in dados.items():
                gdf = converter_multipoint(gdf)
                gdf = calcular_distancias(gdf, ponto_utm)
                gdf = filtrar_por_raio(gdf, raio)
                gdf = calcular_pontuacao(gdf)

                p_total = pontuacao_total(gdf)
                pontuacoes_por_camada[nome] = p_total

            perfis_pontuacao = calcular_todos_os_perfis(
                pontuacoes_por_camada, pesos_personalizados=pesos_personalizados
            )

        st.success("Análise concluída!")

        st.subheader("📊 Pontuação por Perfil")
        cols = st.columns(len(perfis_pontuacao))

        for idx, (perfil, pontuacao) in enumerate(perfis_pontuacao.items()):
            with cols[idx]:
                st.metric(
                    label=f"Perfil: {perfil.capitalize()}",
                    value=f"{(pontuacao*(100/500)):.2f} pontos",
                )

        with st.expander("Ver detalhamento das pontuações por camada"):
            st.json(pontuacoes_por_camada)


if __name__ == "__main__":
    render_mapa()