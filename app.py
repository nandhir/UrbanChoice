from processamento.carregar_dados import carregar_todos
from processamento.distancias import (
    calcular_distancias,
    distancia_media,
    filtrar_por_raio,
    maior_distancia,
    menor_distancia,
    ordenar_por_distancia,
)
from processamento.geometrias import converter_multipoint, criar_ponto
from processamento.pontuacao import (
    calcular_pontuacao,
    calcular_todos_os_perfis,
    pontuacao_media,
    pontuacao_total,
)

# 1. Carrega todos os dados
dados = carregar_todos()

# 2. Ponto de teste (coordenada em Santo André / SIRGAS 2000 UTM 23S)
ponto = criar_ponto(344217.996363955, 7381964.36198292)

RAIO = 3000  # Raio de busca em metros
pontuacoes_por_camada = {}

print("=" * 70)
print("PROCESSAMENTO DAS CAMADAS")
print("=" * 70)

# 3. Processa e pontua cada camada
for nome, gdf in dados.items():
    print(f"\nCamada: {nome}")
    print("-" * 70)

    # Tratamento geométrico e distância
    gdf = converter_multipoint(gdf)
    gdf = calcular_distancias(gdf, ponto)
    gdf = filtrar_por_raio(gdf, RAIO)
    gdf = calcular_pontuacao(gdf)

    # Armazena a pontuação total da camada para o cálculo final dos perfis
    p_total = pontuacao_total(gdf)
    pontuacoes_por_camada[nome] = p_total

    if len(gdf) > 0:
        print(f"Quantidade de locais : {len(gdf)}")
        print(f"Menor distância      : {menor_distancia(gdf):.2f} m")
        print(f"Maior distância      : {maior_distancia(gdf):.2f} m")
        print(f"Distância média      : {distancia_media(gdf):.2f} m")
        print(f"Pontuação total      : {p_total:.2f}")
        print(f"Pontuação média      : {pontuacao_media(gdf):.2f}")

        print(f"\nLocais mais próximos (até {RAIO} m):")
        proximos = ordenar_por_distancia(gdf).head(5)
        print(proximos[["distancia", "pontuacao"]])
    else:
        print(f"Nenhum local encontrado dentro do raio de {RAIO} m.")

# 4. Cálculo final e impressão dos Perfis
print("\n" + "=" * 70)
print("PONTUAÇÃO TOTAL POR PERFIL")
print("=" * 70)

perfis_pontuacao = calcular_todos_os_perfis(pontuacoes_por_camada)

for perfil, pontuacao_final in perfis_pontuacao.items():
    print(f"Perfil {perfil.capitalize():<15}: {pontuacao_final:.2f} pontos")

print("=" * 70)