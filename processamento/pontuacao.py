"""
Funções responsáveis pelo cálculo de pontuações.

Este módulo NÃO realiza leitura de arquivos nem cálculo de distâncias.
Ele apenas transforma distâncias em pontuações.
"""

import geopandas as gpd

"""
Define os pesos utilizados para cada perfil de usuário.

Os pesos devem sempre somar 1.0 (100%).
"""

PERFIS = {

    "idosos": {

        "hospitais": 0.30,
        "atencao_basica_upa_ubs": 0.20,
        "parques-municipais": 0.15,
        "pracas-areas-verdes": 0.10,
        "pontos-onibus-mun-intermun": 0.10,
        "terminais": 0.05,
        "estacoes-trem": 0.05,
        "educacao": 0.05
    },

    "familias": {

        "educacao": 0.35,
        "hospitais": 0.15,
        "atencao_basica_upa_ubs": 0.15,
        "parques-municipais": 0.15,
        "pracas-areas-verdes": 0.10,
        "pontos-onibus-mun-intermun": 0.05,
        "estacoes-trem": 0.03,
        "terminais-onibus": 0.02
    },

    "universitarios": {

        "pontos-onibus-mun-intermun": 0.25,
        "terminais-onibus": 0.20,
        "estacoes-trem": 0.20,
        "atencao_basica_upa_ubs": 0.10,
        "parques-municipais": 0.10,
        "hospitais": 0.05,
        "educacao": 0.05,
        "pracas-areas-verdes": 0.05
    }

}

"""
Funções responsáveis pelo cálculo de pontuações.

Este módulo recebe GeoDataFrames contendo uma coluna
'distancia' e transforma essas distâncias em pontuações.

Também é responsável por combinar as pontuações das
camadas utilizando os pesos definidos para cada perfil.
"""


# ==========================================================
# Pontuação individual
# ==========================================================

def calcular_pontuacao(
        gdf: gpd.GeoDataFrame,
        constante: float = 10000.0
) -> gpd.GeoDataFrame:

    resultado = gdf.copy()

    resultado["pontuacao"] = resultado["distancia"].apply(

        lambda d: constante if d == 0 else constante / d

    )

    return resultado


# ==========================================================
# Estatísticas da camada
# ==========================================================

def pontuacao_total(gdf):

    return gdf["pontuacao"].sum()


def pontuacao_media(gdf):

    return gdf["pontuacao"].mean()


def maior_pontuacao(gdf):

    return gdf["pontuacao"].max()


def ordenar_por_pontuacao(gdf):

    return gdf.sort_values(
        "pontuacao",
        ascending=False
    ).reset_index(drop=True)


# ==========================================================
# Perfis
# ==========================================================

def calcular_perfil(
        pontuacoes_camadas: dict,
        perfil: str
):
    """
    Calcula a pontuação de um perfil.

    Parameters
    ----------
    pontuacoes_camadas : dict

        Exemplo:

        {
            "hospitais": 152.3,
            "parques": 88.1,
            "escolas": 50.9
        }

    perfil : str

        idosos
        familias
        universitarios

    Returns
    -------
    float
    """

    pesos = PERFIS[perfil]

    total = 0.0

    for camada, pontuacao in pontuacoes_camadas.items():

        peso = pesos.get(camada, 0)

        total += pontuacao * peso

    return total


def calcular_todos_os_perfis(
        pontuacoes_camadas: dict
):
    """
    Calcula simultaneamente os três perfis.
    """

    resultado = {}

    for perfil in PERFIS:

        resultado[perfil] = calcular_perfil(
            pontuacoes_camadas,
            perfil
        )

    return resultado