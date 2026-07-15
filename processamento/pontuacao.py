"""
Funções responsáveis pelo cálculo de pontuações.

Este módulo NÃO realiza leitura de arquivos nem cálculo de distâncias.
Ele apenas transforma distâncias em pontuações.
"""

import geopandas as gpd

# ==========================================================
# Constantes
# ==========================================================

CONSTANTE_PONTUACAO = 100.0


# ==========================================================
# Cálculo de pontuação
# ==========================================================

def calcular_pontuacao(
        gdf: gpd.GeoDataFrame,
        constante: float = CONSTANTE_PONTUACAO
) -> gpd.GeoDataFrame:
    """
    Calcula uma pontuação para cada objeto utilizando apenas
    sua distância ao ponto de referência.

    Fórmula:

        pontuacao = constante / distancia

    Caso a distância seja zero, a pontuação é considerada infinita.

    Parameters
    ----------
    gdf : GeoDataFrame
        Deve possuir a coluna 'distancia'.

    constante : float
        Constante utilizada na fórmula.

    Returns
    -------
    GeoDataFrame
        Cópia contendo a coluna 'pontuacao'.
    """

    resultado = gdf.copy()

    resultado["pontuacao"] = resultado["distancia"].apply(
    lambda d: constante if d == 0 else constante / d
)

    return resultado


# ==========================================================
# Estatísticas
# ==========================================================

def pontuacao_total(gdf: gpd.GeoDataFrame) -> float:
    """
    Soma a pontuação de todos os objetos.
    """

    return gdf["pontuacao"].sum()


def pontuacao_media(gdf: gpd.GeoDataFrame) -> float:
    """
    Retorna a pontuação média.
    """

    return gdf["pontuacao"].mean()


def maior_pontuacao(gdf: gpd.GeoDataFrame) -> float:
    """
    Retorna a maior pontuação.
    """

    return gdf["pontuacao"].max()


def ordenar_por_pontuacao(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """
    Ordena do maior para o menor valor de pontuação.
    """

    return gdf.sort_values(
        "pontuacao",
        ascending=False
    ).reset_index(drop=True)