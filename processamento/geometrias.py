"""
Funções auxiliares para manipulação de geometrias.

Este módulo contém apenas operações geométricas.
Não realiza leitura de arquivos nem cálculos de pontuação.
"""

import geopandas as gpd
from shapely.geometry import Point, MultiPoint


def criar_ponto(x, y):
    """
    Cria um objeto Point a partir de coordenadas.
    """

    return Point(x, y)


def converter_multipoint(gdf):
    """
    Converte geometrias MultiPoint contendo um único ponto
    em geometrias Point.

    Retorna um novo GeoDataFrame.
    """

    gdf = gdf.copy()

    def converter(geom):

        if isinstance(geom, MultiPoint):

            pontos = list(geom.geoms)

            if len(pontos) == 1:
                return pontos[0]

        return geom

    gdf["geometry"] = gdf["geometry"].apply(converter)

    return gdf


def validar_geometrias(gdf):
    """
    Verifica se todas as geometrias são válidas.

    Retorna True se todas forem válidas.
    """

    return gdf.geometry.is_valid.all()


def contar_tipos(gdf):
    """
    Retorna a quantidade de cada tipo de geometria.
    """

    return gdf.geom_type.value_counts()


def obter_crs(gdf):
    """
    Retorna o sistema de coordenadas.
    """

    return gdf.crs