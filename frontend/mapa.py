import streamlit as st
import folium
from streamlit_folium import st_folium


def render_mapa():
    """Exibe o mapa interativo, captura o clique do usuário e armazena o raio e as coordenadas no session_state."""
    st.set_page_config(page_title="UrbanChoice", layout="wide")

    st.title("🌍 UrbanChoice")
    st.write(
        "Clique em qualquer ponto do mapa para selecionar uma área de análise."
    )

    # 1. Inicialização do Session State
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

    # 2. Configuração do Raio na Barra Lateral
    st.sidebar.header("Configurações")
    st.session_state.raio_analise = st.sidebar.slider(
        "Raio de análise (metros)",
        min_value=500,
        max_value=10000,
        value=st.session_state.raio_analise,
        step=500,
    )

    # 3. Construção do Mapa Folium
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

    # 4. Exibição e Captura do Clique
    dados_mapa = st_folium(mapa, width=900, height=600)

    if dados_mapa and dados_mapa.get("last_clicked"):
        nova_lat = dados_mapa["last_clicked"]["lat"]
        nova_lon = dados_mapa["last_clicked"]["lng"]

        # Atualiza se o ponto mudou
        if nova_lat != st.session_state.lat or nova_lon != st.session_state.lon:
            st.session_state.lat = nova_lat
            st.session_state.lon = nova_lon
            # Variável com a tupla (lat, lon) pronta para posterior conversão/cálculo de pontuação
            st.session_state.ponto_selecionado = (nova_lat, nova_lon)
            st.rerun()

    # 5. Métricas e Ação de Análise
    st.subheader("Ponto selecionado")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Latitude", f"{st.session_state.lat:.6f}")
    with col2:
        st.metric("Longitude", f"{st.session_state.lon:.6f}")

    if st.button("Analisar área"):
        st.success("Análise iniciada!")

        # Variáveis disponíveis para uso direto ou exportação/cálculo
        ponto = st.session_state.ponto_selecionado
        raio = st.session_state.raio_analise

        st.write("Ponto para conversão (Lat, Lon):", ponto)
        st.write("Raio configurado:", raio, "metros")

        # Exemplo de integração futura com o backend/cálculo de pontuação:
        # ponto_transformado = transformar_coordenadas(ponto)
        # pontuacao = calcular_pontuacao(ponto_transformado, raio)


if __name__ == "__main__":
    render_mapa()