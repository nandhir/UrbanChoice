"""
Módulo responsável pelo carregamento de arquivos geográficos do projeto.

Todas as funções deste módulo retornam GeoDataFrames prontos para uso.
Nenhum processamento geográfico é realizado aqui.
"""

from pathlib import Path

import geopandas as gpd


# -------------------------------------------------------------------
# Caminhos do projeto
# -------------------------------------------------------------------

PASTA_DADOS = Path(__file__).resolve().parent.parent / "dados"


# -------------------------------------------------------------------
# Funções
# -------------------------------------------------------------------

def listar_arquivos():
    """
    Retorna todos os arquivos .gpkg presentes na pasta de dados.

    Returns
    -------
    list[Path]
        Lista contendo os caminhos dos arquivos.
    """

    return sorted(PASTA_DADOS.glob("*.gpkg"))


def carregar_gpkg(nome_arquivo):
    """
    Carrega um GeoPackage da pasta dados.

    Parameters
    ----------
    nome_arquivo : str
        Nome do arquivo (ex.: hospitais.gpkg)

    Returns
    -------
    GeoDataFrame
    """

    caminho = PASTA_DADOS / nome_arquivo

    if not caminho.exists():
        raise FileNotFoundError(
            f"Arquivo não encontrado:\n{caminho}"
        )

    return gpd.read_file(caminho)


def resumo(gdf):
    """
    Exibe um pequeno resumo do GeoDataFrame.
    """

    print("=" * 60)

    print(f"Registros : {len(gdf)}")

    print(f"CRS       : {gdf.crs}")

    print(f"Geometrias:")

    print(gdf.geom_type.value_counts())

    print("\nColunas:")

    for coluna in gdf.columns:
        print(f"  • {coluna}")

    print("=" * 60)


# -------------------------------------------------------------------
# Teste do módulo
# -------------------------------------------------------------------

if __name__ == "__main__":

    print("\nArquivos encontrados:\n")

    arquivos = listar_arquivos()

    for arquivo in arquivos:

        print(f" - {arquivo.name}")

    if arquivos:

        print("\nAbrindo primeiro arquivo apenas como teste...\n")

        gdf = carregar_gpkg(arquivos[0].name)

        resumo(gdf)