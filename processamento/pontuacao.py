"""
Funções responsáveis pelo cálculo de pontuações.
"""

import geopandas as gpd

# Padronização das chaves do dicionário para casar com os nomes dos arquivos .gpkg
PERFIS = {
    "idosos": {
        "hospitais": 0.30,
        "atenção básica (upa e ubs)": 0.20,
        "parques municipais": 0.15,
        "áreas verdes": 0.10,
        "pontos de ônibus": 0.10,
        "terminais de ônibus": 0.05,
        "estações de trem": 0.05,
        "educação": 0.05,
    },
    "familias": {
        "educação": 0.35,
        "hospitais": 0.15,
        "atenção básica (upa e ubs)": 0.15,
        "parques municipais": 0.15,
        "áreas verdes": 0.10,
        "pontos de ônibus": 0.05,
        "estações de trem": 0.03,
        "terminais de ônibus": 0.02,
    },
    "universitarios": {
        "pontos de ônibus": 0.16,
        "terminais de ônibus": 0.13,
        "estações de trem": 0.21,
        "atenção básica (upa e ubs)": 0.12,
        "parques municipais": 0.13,
        "hospitais": 0.10,
        "educação": 0.07,
        "áreas verdes": 0.08,
    },
    "personalizado": {
        "hospitais": 0.125,
        "atenção básica (upa e ubs)": 0.125,
        "parques municipais": 0.125,
        "áreas verdes": 0.125,
        "pontos de ônibus": 0.125,
        "terminais de ônibus": 0.125,
        "estações de trem": 0.125,
        "educação": 0.125,
    },
}


def aplicar_atenuacao(pontuacao_bruta: float) -> float:
    """Aplica penalização/divisão caso a pontuação bruta ultrapasse os limites informados."""
    if pontuacao_bruta > 3000:
        return pontuacao_bruta / 5.0
    elif pontuacao_bruta > 1000:
        return pontuacao_bruta / 2.0
    return pontuacao_bruta


def calcular_pontuacao(
    gdf: gpd.GeoDataFrame, constante: float = 10000.0
) -> gpd.GeoDataFrame:
    resultado = gdf.copy()
    resultado["pontuacao"] = resultado["distancia"].apply(
        lambda d: constante if d == 0 else constante / d
    )
    return resultado


def pontuacao_total(gdf: gpd.GeoDataFrame) -> float:
    if gdf.empty:
        return 0.0
    return gdf["pontuacao"].sum()


def pontuacao_media(gdf: gpd.GeoDataFrame) -> float:
    if gdf.empty:
        return 0.0
    return gdf["pontuacao"].mean()


def maior_pontuacao(gdf: gpd.GeoDataFrame) -> float:
    if gdf.empty:
        return 0.0
    return gdf["pontuacao"].max()


def ordenar_por_pontuacao(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    return gdf.sort_values("pontuacao", ascending=False).reset_index(drop=True)


def calcular_perfil(
    pontuacoes_camadas: dict, perfil: str, pesos_custom: dict = None
) -> float:
    pesos = pesos_custom if (perfil == "personalizado" and pesos_custom) else PERFIS[perfil]
    total = 0.0
    for camada, pontuacao_bruta in pontuacoes_camadas.items():
        pontuacao_ajustada = aplicar_atenuacao(pontuacao_bruta)
        peso = pesos.get(camada, 0)
        total += pontuacao_ajustada * peso
    return total


def calcular_todos_os_perfis(
    pontuacoes_camadas: dict, pesos_personalizados: dict = None
) -> dict:
    resultado = {}
    for perfil in PERFIS:
        resultado[perfil] = calcular_perfil(
            pontuacoes_camadas, perfil, pesos_custom=pesos_personalizados
        )
    return resultado