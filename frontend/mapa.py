import sys
from pathlib import Path

# Adiciona a pasta raiz do projeto ao caminho do Python
RAIZ_PROJETO = Path(__file__).resolve().parent.parent
if str(RAIZ_PROJETO) not in sys.path:
    sys.path.append(str(RAIZ_PROJETO))

import geopandas as gpd
import pyproj
import streamlit as st
import folium
from streamlit_folium import st_folium
from shapely.geometry import Point
from shapely.ops import transform
from folium.plugins import HeatMap
from processamento.recomendador import extrair_dados_heatmap

from processamento.carregar_dados import carregar_todos
from processamento.distancias import calcular_distancias, filtrar_por_raio
from processamento.geometrias import converter_multipoint
from processamento.pontuacao import (
    PERFIS,
    calcular_pontuacao,
    calcular_todos_os_perfis,
    pontuacao_total,
)
from processamento.recomendador import gerar_grid_municipio, calcular_ranking_grid

@st.cache_data
def carregar_dados_cache():
    return carregar_todos()


@st.cache_data
def carregar_limite_santo_andre():
    """Carrega o GeoPackage de delimitação e extrai o contorno de Santo André."""
    caminho_gpkg = RAIZ_PROJETO / "dados_limitacao" / "municipio-santo-andre.gpkg"

    if caminho_gpkg.exists():
        gdf_muns = gpd.read_file(caminho_gpkg)
        gdf_sa = gdf_muns[gdf_muns["NM_MUN"].str.upper() == "SANTO ANDRÉ"].copy()

        # Garante a conversão para WGS84 para compatibilidade com o Folium e Geometria do Shapely
        if gdf_sa.crs is not None and gdf_sa.crs.to_string() != "EPSG:4326":
            gdf_sa = gdf_sa.to_crs(epsg=4326)

        return gdf_sa
    return None


def ponto_esta_dentro_santo_andre(lat: float, lon: float, gdf_sa: gpd.GeoDataFrame) -> bool:
    """Verifica se a coordenada (lat, lon) está contida no limite municipal."""
    if gdf_sa is None or gdf_sa.empty:
        return True  # Caso não exista a camada de limite, permite a análise normalmente

    ponto = Point(lon, lat)  # Shapely usa (x, y) = (lon, lat)
    uniao_geometrias = gdf_sa.geometry.unary_union
    return uniao_geometrias.contains(ponto)


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

    NOMES_EXIBICAO = {
        "hospitais": "Hospitais",
        "atencao_basica_upa_ubs": "Atenção Básica (UPA e UBS)",
        "parques-municipais": "Parques Municipais",
        "pracas-areas-verdes": "Áreas Verdes",
        "pontos-onibus-mun-intermun": "Pontos de Ônibus",
        "terminais-onibus": "Terminais de Ônibus",
        "estacoes-trem": "Estações de Trem",
        "educacao": "Educação",
    }

    # Pesos do Perfil Personalizado na Sidebar (com exibição padronizada)
    st.sidebar.subheader("Perfil Personalizado")
    pesos_brutos = {}
    
    for camada in camadas_disponiveis:
        nome_rotulo = NOMES_EXIBICAO.get(camada, camada)
        valor_padrao = PERFIS["personalizado"].get(camada, 0.10)
        pesos_brutos[camada] = st.sidebar.number_input(
            f"{nome_rotulo}",
            min_value=0.0,
            max_value=1.0,
            value=float(valor_padrao),
            step=0.05,
            format="%.3f",
            key=f"input_{camada}"
        )

    soma_pesos = sum(pesos_brutos.values())

    # Exibe indicador da soma dos pesos para o usuário
    if abs(soma_pesos - 1.0) < 1e-4:
        st.sidebar.caption(f"✅ **Soma dos pesos:** {soma_pesos:.2f} / 1.00")
        pesos_personalizados = pesos_brutos
    elif soma_pesos > 1.0:
        st.sidebar.caption(f"⚠️ **Soma atual:** {soma_pesos:.2f} (Valores serão normalizados para somar 1.0)")
        # Normalização matemática proporcional: w_i / sum(w)
        pesos_personalizados = {k: v / soma_pesos for k, v in pesos_brutos.items()}
    else:
        st.sidebar.caption(f"ℹ️ **Soma atual:** {soma_pesos:.2f} / 1.00")
        pesos_personalizados = pesos_brutos
    # Construção do Mapa
    mapa = folium.Map(
        location=[st.session_state.lat, st.session_state.lon], zoom_start=12
    )

    # Renderiza o limite municipal de Santo André se disponível
    gdf_sa = carregar_limite_santo_andre()
    if gdf_sa is not None and not gdf_sa.empty:
        folium.GeoJson(
            gdf_sa,
            name="Delimitação de Santo André",
            style_function=lambda feature: {
                "fillColor": "#3186cc",
                "color": "#1c3d5a",
                "weight": 3,
                "fillOpacity": 0.2,
            },
            tooltip="Município de Santo André",
        ).add_to(mapa)

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
        # Validação de localização dentro do município de Santo André
        if not ponto_esta_dentro_santo_andre(st.session_state.lat, st.session_state.lon, gdf_sa):
            st.warning("⚠️ Fora da zona delimitada")
        else:
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

            st.success("Análise concluída com sucesso!")

            # =========================================================
            # 1. Identificação do Perfil Predominante (Melhor Encaixe)
            # =========================================================
            # Ignora o perfil 'personalizado' na escolha automática do melhor perfil
            perfis_predefinidos = {
                p: v for p, v in perfis_pontuacao.items() if p != "personalizado"
            }
            melhor_perfil = max(perfis_predefinidos, key=perfis_predefinidos.get)
            maior_nota = perfis_predefinidos[melhor_perfil] * (100 / 500)

            st.markdown("---")
            st.subheader("🎯 Perfil Recomendado")
            st.info(
                f"🌟 O local selecionado apresenta excelente vocação para o perfil "
                f"**{melhor_perfil.capitalize()}** com pontuação de **{maior_nota:.2f} / 100**."
            )

            # =========================================================
            # 2. Exibição Métrica dos Perfis
            # =========================================================
            st.subheader("📊 Pontuação por Perfil")
            cols = st.columns(len(perfis_pontuacao))
            for idx, (perfil, pontuacao) in enumerate(perfis_pontuacao.items()):
                nota_escala = pontuacao * (100 / 500)
                with cols[idx]:
                    st.metric(
                        label=f"Perfil: {perfil.capitalize()}",
                        value=f"{nota_escala:.2f} pts",
                        delta="Melhor Opção" if perfil == melhor_perfil else None,
                    )

            # =========================================================
            # 3. Exibição Detalhada dos Dados (Abas)
            # =========================================================
            st.markdown("---")
            st.subheader("🔍 Detalhamento das Camadas")

            tab1, tab2, tab3 = st.tabs(["📊 Visão Geral por Camada", "📋 Tabela de Dados", "📄 JSON Bruto"])

            with tab1:
                import pandas as pd
                
                # Monta DataFrame com dados formatados
                df_detalhado = pd.DataFrame([
                    {
                        "Camada": NOMES_EXIBICAO.get(nome, nome.replace("_", " ").title()),
                        "Chave": nome,
                        "Pontuação Bruta Acumulada": round(p_bruta, 2),
                    }
                    for nome, p_bruta in pontuacoes_por_camada.items()
                ])

                # Exibe gráfico de barras interativo nativo do Streamlit
                st.bar_chart(
                    data=df_detalhado,
                    x="Camada",
                    y="Pontuação Bruta Acumulada",
                    color="#3186cc",
                )

            with tab2:
                st.dataframe(
                    df_detalhado[["Camada", "Pontuação Bruta Acumulada"]],
                    use_container_width=True,
                    hide_index=True,
                )

            with tab3:
                st.json(pontuacoes_por_camada)
    aba_analise, aba_recomendacao, aba_heatmap = st.tabs(["📍 Análise de Ponto Específico", "🏆 Recomendador de Locais", "🔥 Mapa de Calor"])

    with aba_analise:
    # Todo o código anterior de renderização do mapa folium, st_folium e botão "Analisar área" fica aqui
    # ...

       with aba_recomendacao:
        st.header("🎯 Encontre as Melhores Zonas por Perfil")
        st.write("O recomendador analisa uma grade de pontos por todo o município de Santo André para encontrar as áreas com maior infraestrutura para cada perfil.")

        col_rec1, col_rec2 = st.columns([2, 1])
    with col_rec1:
        perfil_alvo = st.selectbox(
            "Selecione o Perfil Desejado:",
            options=list(PERFIS.keys()),
            format_func=lambda x: x.capitalize()
        )
    with col_rec2:
        top_n = st.slider("Quantidade de Recomendações:", min_value=3, max_value=10, value=5)

    if st.button("🔍 Gerar Recomendação de Locais", type="primary"):
        gdf_sa = carregar_limite_santo_andre()
        
        if gdf_sa is None or gdf_sa.empty:
            st.error("Não foi possível carregar a delimitação de Santo André para gerar o grid.")
        else:
            with st.spinner("Mapeando a cidade e calculando recomendações..."):
                # Gera grid de ~800m para equilíbrio entre performance e cobertura
                pontos_grid = gerar_grid_municipio(gdf_sa, espacamento_metros=800.0)
                
                # Calcula notas do grid e salva no session_state para manter a tabela entre re-renders
                st.session_state.df_ranking_rec = calcular_ranking_grid(
                    dados, 
                    pontos_grid, 
                    raio_analise=st.session_state.raio_analise,
                    pesos_personalizados=pesos_personalizados
                )

    # Exibe as recomendações salvas no session_state
    if "df_ranking_rec" in st.session_state and not st.session_state.df_ranking_rec.empty:
        df_ranking = st.session_state.df_ranking_rec
        df_top = df_ranking.sort_values(by=perfil_alvo, ascending=False).head(top_n)

        st.success(f"Top {top_n} regiões encontradas para o perfil **{perfil_alvo.capitalize()}**!")

        # Exibição dos cards de resultado
        for pos, (_, row) in enumerate(df_top.iterrows(), 1):
            with st.container():
                c1, c2, c3, c4 = st.columns([1, 3, 2, 2])
                with c1:
                    st.markdown(f"### #{pos}")
                with c2:
                    st.write(f"**Coordenadas:**")
                    st.caption(f"Lat: `{row['lat']:.5f}` | Lon: `{row['lon']:.5f}`")
                with c3:
                    st.metric("Pontuação", f"{row[perfil_alvo]} pts")
                with c4:
                    # Botão funcional para focar no mapa
                    if st.button("📍 Ver no Mapa", key=f"btn_focar_{pos}"):
                        st.session_state.lat = row['lat']
                        st.session_state.lon = row['lon']
                        st.session_state.ponto_selecionado = (row['lat'], row['lon'])
                        st.rerun()
                
                st.divider()

        # Tabela resumida para inspeção
        with st.expander("Ver tabela completa do ranking"):
            st.dataframe(
                df_top[["lat", "lon"] + list(PERFIS.keys())],
                use_container_width=True,
                hide_index=True
            )


            with aba_heatmap:
             st.header("🔥 Mapa de Calor de Acessibilidade")
    st.write(
        "Visualize a distribuição de infraestrutura e acessibilidade urbana em toda a cidade "
        "com base no perfil selecionado."
    )

    col_h1, col_h2 = st.columns([2, 1])
    with col_h1:
        perfil_heatmap = st.selectbox(
            "Selecione o Perfil para o Mapa de Calor:",
            options=list(PERFIS.keys()),
            format_func=lambda x: x.capitalize(),
            key="select_perfil_heatmap"
        )
    with col_h2:
        raio_difusao = st.slider("Raio de Difusão das Manchas (px):", min_value=10, max_value=40, value=25)

    if st.button("🌐 Gerar Mapa de Calor", type="primary"):
        gdf_sa = carregar_limite_santo_andre()
        
        if gdf_sa is None or gdf_sa.empty:
            st.error("Não foi possível carregar a delimitação de Santo André.")
        else:
            with st.spinner("Calculando malha da cidade e construindo mapa de calor..."):
                # 1. Utiliza um grid mais denso (ex: 500m) para o heatmap ficar suave
                pontos_grid = gerar_grid_municipio(gdf_sa, espacamento_metros=500.0)
                
                # 2. Reutiliza ou calcula os dados do grid
                df_grid = calcular_ranking_grid(
                    dados, 
                    pontos_grid, 
                    raio_analise=st.session_state.raio_analise,
                    pesos_personalizados=pesos_personalizados
                )
                
                # Salva para não recalcular se trocar parâmetros visuais
                st.session_state.df_grid_heatmap = df_grid

    # Se os dados do heatmap já existirem no session_state, renderiza o mapa
    if "df_grid_heatmap" in st.session_state and not st.session_state.df_grid_heatmap.empty:
        df_grid = st.session_state.df_grid_heatmap
        dados_heat = extrair_dados_heatmap(df_grid, perfil_heatmap)

        # Criar mapa base focado em Santo André
        mapa_heat = folium.Map(
            location=[-23.644912, -46.527910], 
            zoom_start=12,
            tiles="cartodbpositron" # Estilo mais limpo para destacar o heatmap
        )

        # Adicionar o contorno do município
        gdf_sa = carregar_limite_santo_andre()
        if gdf_sa is not None and not gdf_sa.empty:
            folium.GeoJson(
                gdf_sa,
                style_function=lambda x: {
                    "color": "#1c3d5a", 
                    "weight": 2, 
                    "fillOpacity": 0.05
                }
            ).add_to(mapa_heat)

        # Adiciona a camada de calor (HeatMap)
        HeatMap(
            dados_heat,
            radius=raio_difusao,
            blur=15,
            max_zoom=13,
            min_opacity=0.3,
            gradient={0.2: 'blue', 0.4: 'lime', 0.6: 'yellow', 1.0: 'red'}
        ).add_to(mapa_heat)

        # Renderiza o mapa com largura total
        st_folium(mapa_heat, width=900, height=600)

if __name__ == "__main__":
    render_mapa()