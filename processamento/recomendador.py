"""
Módulo responsável pela geração de grid espacial, recomendação de áreas
e formatação de dados para visualização em Mapa de Calor (Heatmap).
"""

import numpy as np
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point

from processamento.geometrias import converter_multipoint
from processamento.distancias import calcular_distancias, filtrar_por_raio
from processamento.pontuacao import calcular_pontuacao, pontuacao_total, calcular_todos_os_perfis


def gerar_grid_municipio(gdf_limite: gpd.GeoDataFrame, espacamento_metros: float = 600.0) -> list:
    """
    Gera uma grade de pontos espalhados geograficamente dentro do limite do município.
    
    Parameters
    ----------
    gdf_limite : GeoDataFrame
        Deve conter o polígono do município em EPSG:4326.
    espacamento_metros : float
        Distância aproximada entre os pontos da grade (em metros).
    """
    if gdf_limite is None or gdf_limite.empty:
        return []

    # Converte temporariamente para UTM para medir em metros
    gdf_utm = gdf_limite.to_crs(epsg=31983)
    minx, miny, maxx, maxy = gdf_utm.total_bounds
    
    x_coords = np.arange(minx, maxx, espacamento_metros)
    y_coords = np.arange(miny, maxy, espacamento_metros)
    
    uniao_geometria = gdf_utm.geometry.unary_union
    pontos_grid_utm = []

    for x in x_coords:
        for y in y_coords:
            p = Point(x, y)
            if uniao_geometria.contains(p):
                pontos_grid_utm.append(p)
                
    return pontos_grid_utm


def calcular_ranking_grid(
    dados_camadas: dict, 
    pontos_grid_utm: list, 
    raio_analise: float = 3000.0,
    pesos_personalizados: dict = None
) -> pd.DataFrame:
    """
    Varre os pontos do grid, calcula a pontuação para cada perfil e retorna um DataFrame ranqueado.
    """
    resultados = []

    # Pré-processa camadas uma única vez para otimizar velocidade
    camadas_convertidas = {nome: converter_multipoint(gdf) for nome, gdf in dados_camadas.items()}

    for idx, ponto_utm in enumerate(pontos_grid_utm):
        # Transforma ponto UTM de volta para Lat/Lon (WGS84)
        gdf_ponto = gpd.GeoDataFrame(geometry=[ponto_utm], crs="EPSG:31983").to_crs(epsg=4326)
        lon_wgs84 = gdf_ponto.geometry.iloc[0].x
        lat_wgs84 = gdf_ponto.geometry.iloc[0].y

        pontuacoes_por_camada = {}

        for nome, gdf in camadas_convertidas.items():
            gdf_dist = calcular_distancias(gdf, ponto_utm)
            gdf_raio = filtrar_por_raio(gdf_dist, raio_analise)
            gdf_pont = calcular_pontuacao(gdf_raio)
            pontuacoes_por_camada[nome] = pontuacao_total(gdf_pont)

        perfis_pontuacao = calcular_todos_os_perfis(
            pontuacoes_por_camada, pesos_personalizados=pesos_personalizados
        )

        linha = {
            "id": idx + 1,
            "lat": lat_wgs84,
            "lon": lon_wgs84,
            "point_utm": ponto_utm,
        }
        for perfil, score in perfis_pontuacao.items():
            linha[perfil] = round(score * (100 / 500), 2)

        resultados.append(linha)

    return pd.DataFrame(resultados)


def extrair_dados_heatmap(df_ranking: pd.DataFrame, perfil: str) -> list:
    """
    Extrai uma lista de triplas [lat, lon, intensidade] formatada para o plugin HeatMap do Folium.
    
    Parameters
    ----------
    df_ranking : pd.DataFrame
        DataFrame gerado pela função `calcular_ranking_grid`.
    perfil : str
        Nome do perfil selecionado (ex: 'idosos', 'universitarios', 'familias').
    """
    if df_ranking.empty or perfil not in df_ranking.columns:
        return []

    # O Folium HeatMap espera uma lista de listas: [[lat, lon, peso], ...]
    dados_heat = df_ranking[["lat", "lon", perfil]].values.tolist()
    return dados_heat