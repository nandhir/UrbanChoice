"""
Funções responsáveis apenas pelo cálculo de distâncias.

Este módulo NÃO conhece hospitais, escolas, pesos ou pontuações.
Sua única responsabilidade é calcular distâncias entre um ponto de
referência e as geometrias de um GeoDataFrame.
"""

import geopandas as gpd
from shapely.geometry import Point


def calcular_distancias(gdf: gpd.GeoDataFrame,
                         ponto_referencia: Point) -> gpd.GeoDataFrame:
    """
    Calcula a distância entre um ponto de referência e todas as
    geometrias do GeoDataFrame.

    Parameters
    ----------
    gdf : GeoDataFrame
        Conjunto de objetos geográficos.

    ponto_referencia : Point
        Coordenada escolhida pelo usuário.

    Returns
    -------
    GeoDataFrame
        Cópia do GeoDataFrame contendo uma nova coluna:
        'distancia' (em metros).
    """

    resultado = gdf.copy()

    resultado["distancia"] = resultado.geometry.distance(ponto_referencia)

    return resultado


def menor_distancia(gdf: gpd.GeoDataFrame) -> float:
    """
    Retorna a menor distância encontrada.
    """

    return gdf["distancia"].min()


def maior_distancia(gdf: gpd.GeoDataFrame) -> float:
    """
    Retorna a maior distância encontrada.
    """

    return gdf["distancia"].max()


def distancia_media(gdf: gpd.GeoDataFrame) -> float:
    """
    Retorna a distância média.
    """

    return gdf["distancia"].mean()


def ordenar_por_distancia(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """
    Retorna um novo GeoDataFrame ordenado da menor
    para a maior distância.
    """

    return gdf.sort_values("distancia").reset_index(drop=True)