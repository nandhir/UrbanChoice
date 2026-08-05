"""
Módulo responsável pelo cálculo de pontuações de acessibilidade urbana.

Utiliza modelo de Decaimento Gaussiano para pontuação individual por distância
e Saturação Logarítmica para representar retornos marginais decrescentes por camada.
"""

import numpy as np
import geopandas as gpd

# Padronização das chaves com underscores (_) para alinhar com os arquivos .gpkg
PERFIS = {
    "idosos": {
        "hospitais": 0.30,
        "atencao_basica_upa_ubs": 0.20,
        "parques_municipais": 0.15,
        "areas_verdes": 0.10,
        "pontos_de_onibus": 0.10,
        "terminais_de_onibus": 0.05,
        "estacoes_de_trem": 0.05,
        "educacao": 0.05,
    },
    "familias": {
        "educacao": 0.35,
        "hospitais": 0.15,
        "atencao_basica_upa_ubs": 0.15,
        "parques_municipais": 0.15,
        "areas_verdes": 0.10,
        "pontos_de_onibus": 0.05,
        "estacoes_de_trem": 0.03,
        "terminais_de_onibus": 0.02,
    },
    "universitarios": {
        "pontos_de_onibus": 0.17,
        "terminais_de_onibus": 0.13,
        "estacoes_de_trem": 0.21,
        "atencao_basica_upa_ubs": 0.12,
        "parques_municipais": 0.13,
        "hospitais": 0.09,
        "educacao": 0.07,
        "areas_verdes": 0.08,
    },
    "personalizado": {
        "hospitais": 0.125,
        "atencao_basica_upa_ubs": 0.125,
        "parques_municipais": 0.125,
        "areas_verdes": 0.125,
        "pontos_de_onibus": 0.125,
        "terminais_de_onibus": 0.125,
        "estacoes_de_trem": 0.125,
        "educacao": 0.125,
    },
}


def aplicar_atenuacao(pontuacao_bruta: float, k_sat: float = 300.0) -> float:
    """
    Aplica curva de saturação logarítmica (retornos decrescentes contínuos).
    A(S) = k_sat * ln(1 + S / k_sat)
    """
    if pontuacao_bruta <= 0:
        return 0.0
    return float(k_sat * np.log1p(pontuacao_bruta / k_sat))


def calcular_pontuacao(
    gdf: gpd.GeoDataFrame, 
    sigma: float = 600.0, 
    k: float = 100.0
) -> gpd.GeoDataFrame:
    """
    Calcula a pontuação de cada equipamento usando Kernel Gaussiano.
    P_i = k * exp(- (d^2) / (2 * sigma^2))
    """
    resultado = gdf.copy()
    if resultado.empty or "distancia" not in resultado.columns:
        resultado["pontuacao"] = 0.0
        return resultado

    distancias = resultado["distancia"].values
    resultado["pontuacao"] = k * np.exp(- (distancias ** 2) / (2 * (sigma ** 2)))
    return resultado


def pontuacao_total(gdf: gpd.GeoDataFrame) -> float:
    """Retorna a soma das pontuações dos equipamentos presentes no GeoDataFrame."""
    if gdf.empty:
        return 0.0
    return float(gdf["pontuacao"].sum())


def pontuacao_media(gdf: gpd.GeoDataFrame) -> float:
    """Retorna a pontuação média dos equipamentos."""
    if gdf.empty:
        return 0.0
    return float(gdf["pontuacao"].mean())


def maior_pontuacao(gdf: gpd.GeoDataFrame) -> float:
    """Retorna a maior pontuação individual encontrada."""
    if gdf.empty:
        return 0.0
    return float(gdf["pontuacao"].max())


def ordenar_por_pontuacao(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Ordena o GeoDataFrame da maior para a menor pontuação."""
    return gdf.sort_values("pontuacao", ascending=False).reset_index(drop=True)


def calcular_perfil(
    pontuacoes_camadas: dict, perfil: str, pesos_custom: dict = None
) -> float:
    """Calcula a pontuação ponderada final para um perfil específico."""
    pesos = pesos_custom if (perfil == "personalizado" and pesos_custom) else PERFIS.get(perfil, {})
    total = 0.0
    
    for camada, pontuacao_bruta in pontuacoes_camadas.items():
        pontuacao_ajustada = aplicar_atenuacao(pontuacao_bruta)
        peso = pesos.get(camada, 0.0)
        total += pontuacao_ajustada * peso
        
    return total


def calcular_todos_os_perfis(
    pontuacoes_camadas: dict, pesos_personalizados: dict = None
) -> dict:
    """Calcula a pontuação para todos os perfis disponíveis."""
    resultado = {}
    for perfil in PERFIS:
        resultado[perfil] = calcular_perfil(
            pontuacoes_camadas, perfil, pesos_custom=pesos_personalizados
        )
    return resultado