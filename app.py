from processamento.carregar_dados import carregar_todos
from processamento.geometrias import criar_ponto, converter_multipoint
from processamento.distancias import (
    calcular_distancias,
    filtrar_por_raio,
    menor_distancia,
    maior_distancia,
    distancia_media,
    ordenar_por_distancia
)
from processamento.pontuacao import (
    calcular_pontuacao,
    pontuacao_total,
    pontuacao_media
)

# ==========================================================
# Carrega todos os dados
# ==========================================================

dados = carregar_todos()

# ==========================================================
# Ponto de teste
# (coordenada do primeiro hospital)
# ==========================================================

ponto = criar_ponto(
    344217.996363955,
    7381964.36198292
)

print("=" * 70)
print("TESTE DO PROTÓTIPO")
print("=" * 70)

# ==========================================================
# Testa cada camada
# ==========================================================

for nome, gdf in dados.items():

    RAIO = 1000  # metros

    print(f"\nCamada: {nome}")
    print("-" * 70)

    # Converte MultiPoint -> Point
    gdf = converter_multipoint(gdf)

    # Distâncias
    gdf = calcular_distancias(gdf, ponto)

    #Filtra por raio de 1000 metros
    gdf = filtrar_por_raio(gdf, RAIO)

    # Pontuações
    gdf = calcular_pontuacao(gdf)

    print(f"Quantidade de locais : {len(gdf)}")
    print(f"Menor distância      : {menor_distancia(gdf):.2f} m")
    print(f"Maior distância      : {maior_distancia(gdf):.2f} m")
    print(f"Distância média      : {distancia_media(gdf):.2f} m")

    print()

    print(f"Pontuação total      : {pontuacao_total(gdf):.4f}")
    print(f"Pontuação média      : {pontuacao_media(gdf):.4f}")

    print("\nlocais mais próximos (até 1000 m de distância):")

    proximos = ordenar_por_distancia(gdf).head(5)

    print(
        proximos[
            [
                "distancia",
                "pontuacao"
            ]
        ]
    )

print("\n")
print("=" * 70)
print("FIM DO TESTE")
print("=" * 70)