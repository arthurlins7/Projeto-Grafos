# [IA] Claude - implementacao escrita com apoio de IA, revisada e testada pelo grupo

import json
from pathlib import Path

from src.graphs.io import ler_mapa, salvar_arestas_csv, salvar_graus_csv
from src.graphs.estados import (
    NO_ALVO,
    calcular_teto_teorico,
    construir_grafo_estados,
    construir_grafo_posicoes,
    decompor_estado,
    grafo_estados_sem_alvo,
)


PASTA_MAPAS = Path("data/mapas")
PASTA_SAIDA = Path("out/parte1")


def listar_mapas(pasta=PASTA_MAPAS):
    return sorted(Path(pasta).glob("*.txt"))


def nome_curto(caminho):
    # "data/mapas/m03_tres_chaves.txt" -> "m03"
    return Path(caminho).stem.split("_")[0]


def salvar_json(dados, caminho):
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with open(caminho, "w", encoding="utf-8") as arquivo:
        json.dump(dados, arquivo, ensure_ascii=False, indent=2)


def metricas_do_mapa(linhas):
    g_pos = construir_grafo_posicoes(linhas)
    g_est = grafo_estados_sem_alvo(construir_grafo_estados(linhas))
    teto = calcular_teto_teorico(linhas)
    return {
        "G_pos": g_pos.metricas(),
        "G_est": g_est.metricas(),
        "teto_teorico": teto,
        "taxa_ocupacao": g_est.ordem() / teto,
    }


def camadas_do_mapa(g_est):
    # g_est aqui ja vem sem o ALVO
    camada_de = {}
    nos_por_camada = {}
    for no in g_est.nos():
        posicao, chaves, bonus = decompor_estado(no)
        camada_de[no] = chaves
        if chaves not in nos_por_camada:
            nos_por_camada[chaves] = []
        nos_por_camada[chaves].append(no)

    camadas = {}
    for chaves, lista in nos_por_camada.items():
        camadas[chaves] = g_est.subgrafo_induzido(lista).metricas()

    arcos_entre = 0
    casas = {}
    for origem in g_est.nos():
        for destino, peso, mov, casa in g_est.vizinhos(origem):
            if camada_de[origem] != camada_de[destino]:
                arcos_entre += 1
                posicao, chaves, bonus = decompor_estado(destino)
                chave_casa = f"({posicao[0]},{posicao[1]}) {casa}"
                casas[chave_casa] = casas.get(chave_casa, 0) + 1

    return {
        "camadas": camadas,
        "arcos_entre_camadas": arcos_entre,
        "casas_que_mudam_de_camada": casas,
    }


def gerar_arestas_metricas_camadas(pasta_mapas=PASTA_MAPAS, pasta_saida=PASTA_SAIDA):
    pasta_saida = Path(pasta_saida)
    metricas = {}
    camadas = {}

    for caminho in listar_mapas(pasta_mapas):
        nome = nome_curto(caminho)
        linhas = ler_mapa(caminho)
        g_est = construir_grafo_estados(linhas)

        salvar_arestas_csv(g_est, pasta_saida / f"arestas_{nome}.csv")
        salvar_graus_csv(g_est, pasta_saida / f"graus_{nome}.csv")

        metricas[nome] = metricas_do_mapa(linhas)
        camadas[nome] = camadas_do_mapa(grafo_estados_sem_alvo(g_est))

    salvar_json(metricas, pasta_saida / "metricas_global.json")
    salvar_json(camadas, pasta_saida / "camadas.json")
    return metricas, camadas


if __name__ == "__main__":
    gerar_arestas_metricas_camadas()
    print(f"Arquivos gerados em {PASTA_SAIDA}/")