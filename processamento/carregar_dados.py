"""
Módulo responsável pelo carregamento dos dados geográficos.

Este módulo NÃO conhece hospitais, escolas ou qualquer outro tipo de
informação. Ele apenas localiza todos os arquivos .gpkg presentes na
pasta 'dados', carrega cada um deles e os disponibiliza em um
dicionário.

Cada chave do dicionário corresponde ao nome do arquivo (sem extensão),
e o valor é um GeoDataFrame.
"""

from pathlib import Path
import geopandas as gpd

# ==========================================================
# Caminhos do projeto
# ==========================================================

PASTA_DADOS = Path(__file__).resolve().parent.parent / "dados"


# ==========================================================
# Funções internas
# ==========================================================

def listar_arquivos():
    """
    Retorna todos os arquivos .gpkg presentes na pasta dados.
    """

    return sorted(PASTA_DADOS.glob("*.gpkg"))


def carregar_gpkg(caminho):
    """
    Carrega um único arquivo GeoPackage.

    Parameters
    ----------
    caminho : Path

    Returns
    -------
    GeoDataFrame
    """

    return gpd.read_file(caminho)


# ==========================================================
# Função principal
# ==========================================================

def carregar_todos():
    """
    Carrega automaticamente todos os GeoPackages presentes
    na pasta 'dados'.

    Returns
    -------
    dict

    Exemplo:

    {
        "hospitais": GeoDataFrame,
        "upas_ubs": GeoDataFrame,
        "escolas": GeoDataFrame
    }
    """

    dados = {}

    arquivos = listar_arquivos()

    for arquivo in arquivos:

        nome = arquivo.stem.lower()

        dados[nome] = carregar_gpkg(arquivo)

    return dados


# ==========================================================
# Funções auxiliares
# ==========================================================

def resumo(gdf):
    """
    Exibe um resumo de um GeoDataFrame.
    """

    print(f"Registros : {len(gdf)}")
    print(f"CRS       : {gdf.crs}")

    print("\nTipos de geometria:")

    print(gdf.geom_type.value_counts())

    print("\nColunas:")

    for coluna in gdf.columns:
        print(f" - {coluna}")


def resumo_geral(dados):
    """
    Exibe um resumo de todas as camadas carregadas.
    """

    print("=" * 70)
    print("CAMADAS CARREGADAS")
    print("=" * 70)

    for nome, gdf in dados.items():

        print(f"\nCamada: {nome}")

        resumo(gdf)

        print("-" * 70)


# ==========================================================
# Teste do módulo
# ==========================================================

if __name__ == "__main__":

    dados = carregar_todos()

    resumo_geral(dados)