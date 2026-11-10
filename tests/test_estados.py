# [IA] Claude - sugestao de estrutura de casos de teste (pytest) conferidos a mao pelo grupo
from pathlib import Path

import pytest

from src.graphs.algorithms import bellman_ford, bfs, dijkstra, montar_caminho
from src.graphs.estados import (
    NO_ALVO,
    calcular_teto_teorico,
    construir_grafo_estados,
    construir_grafo_posicoes,
    decompor_estado,
    formatar_estado,
    grafo_estados_sem_alvo,
    indexar_bonus,
)
from src.graphs.io import ler_mapa


# Mapa minimo 4x6 do grupo (calculado a mao):
#   ######
#   #S.AG#
#   #.a###
#   ######
# Casas livres: (1,1)=S, (1,2)=., (1,3)=A, (1,4)=G, (2,1)=., (2,2)=a -> 6 casas
# Chaves: {'a'} (1 chave), Bonus: 0 -> Teto teorico = 6 * 2^1 * 2^0 = 12
# Camada '-' (sem chave): (1,1), (1,2), (2,1) -> 3 estados e 6 arcos saindo deles
# Camada 'a' (com chave): (2,2), (1,2), (2,1), (1,3), (1,1), (1,4) -> 6 estados e 11 arcos
# Total sem ALVO: 9 estados alcancaveis e 17 arcos dirigidos.
MAPA_MINIMO_GRUPO = [
    "######",
    "#S.AG#",
    "#.a###",
    "######",
]


def test_formatar_e_decompor_estado():
    assert formatar_estado(1, 1) == "(1,1)|-|{}"
    assert formatar_estado(3, 5, {"b", "a"}, {2, 0}) == "(3,5)|ab|{0,2}"

    pos, chaves, bonus = decompor_estado("(3,5)|ab|{0,2}")
    assert pos == (3, 5)
    assert chaves == "ab"
    assert bonus == (0, 2)

    pos_ini, chaves_ini, bonus_ini = decompor_estado("(1,1)|-|{}")
    assert pos_ini == (1, 1)
    assert chaves_ini == "-"
    assert bonus_ini == ()


def test_mapa_minimo_calculado_a_mao():
    assert calcular_teto_teorico(MAPA_MINIMO_GRUPO) == 12

    g_sem_alvo = construir_grafo_estados(MAPA_MINIMO_GRUPO, incluir_alvo=False)
    assert g_sem_alvo.ordem() == 9
    assert g_sem_alvo.tamanho() == 17

    g_com_alvo = construir_grafo_estados(MAPA_MINIMO_GRUPO, incluir_alvo=True)
    assert g_com_alvo.ordem() == 10
    assert g_com_alvo.tamanho() == 18
    assert g_com_alvo.vizinhos("(1,4)|a|{}") == [(NO_ALVO, 0, "", "G")]

    sub = grafo_estados_sem_alvo(g_com_alvo)
    assert sub.ordem() == 9
    assert sub.tamanho() == 17


def test_esteira_apontando_para_parede_gera_estado_sem_saida():
    # Em (1,2) ha uma esteira '>' apontando para '#' em (1,3)
    linhas = [
        "######",
        "#S>#G#",
        "######",
    ]
    g = construir_grafo_estados(linhas, incluir_alvo=False)
    estado_esteira = "(1,2)|-|{}"
    assert g.tem_no(estado_esteira)
    assert g.grau_saida(estado_esteira) == 0
    assert g.vizinhos(estado_esteira) == []


def test_esteira_so_permite_movimento_na_direcao_da_seta():
    linhas = [
        "#####",
        "#...#",
        "#.S.#",
        "#.>.#",
        "#..G#",
        "#####",
    ]
    g = construir_grafo_estados(linhas, incluir_alvo=False)
    # Na casa (3,2)='>', mesmo tendo '.' acima, abaixo e a esquerda, so pode ir para L=(3,3)
    vizinhos = g.vizinhos("(3,2)|-|{}")
    assert vizinhos == [("(3,3)|-|{}", 1, "L", ".")]


def test_coletar_chave_muda_de_camada_e_abre_porta():
    g = construir_grafo_estados(MAPA_MINIMO_GRUPO, incluir_alvo=True)

    # Sem a chave 'a', de (1,2)|-|{} nao existe arco para a porta A em (1,3),
    # mas o movimento S para (2,2)='a' muda o rotulo de '-' para 'a'
    viz_12_sem_chave = g.vizinhos("(1,2)|-|{}")
    assert ("(2,2)|a|{}", 1, "S", "a") in viz_12_sem_chave
    assert all( not dest.startswith("(1,3)") for dest, _, _, _ in viz_12_sem_chave )

    # Com a chave 'a', de (1,2)|a|{} o movimento L entra na porta A em (1,3)|a|{}
    viz_12_com_chave = g.vizinhos("(1,2)|a|{}")
    assert ("(1,3)|a|{}", 1, "L", "A") in viz_12_com_chave


def test_chaves_ordenadas_alfabeticamente_no_rotulo():
    linhas = [
        "######",
        "#SbaG#",
        "######",
    ]
    g = construir_grafo_estados(linhas, incluir_alvo=False)
    assert g.tem_no("(1,2)|b|{}")
    assert g.tem_no("(1,3)|ab|{}")


def test_bonus_consumido_uma_vez_em_ordem_de_leitura():
    # Dois bonus '+': (1,2) tem indice 0 e (2,1) tem indice 1
    linhas = [
        "#####",
        "#S+.#",
        "#+G.#",
        "#####",
    ]
    assert indexar_bonus(linhas) == {(1, 2): 0, (2, 1): 1}

    g = construir_grafo_estados(linhas, incluir_alvo=False)
    # Primeira entrada em (1,2) custa -4 e marca bonus {0}
    assert ("(1,2)|-|{0}", -4, "L", "+") in g.vizinhos("(1,1)|-|{}")
    # Voltar para (1,1) e entrar de novo em (1,2) ja tendo {0} custa 1 (vira chao)
    assert ("(1,2)|-|{0}", 1, "L", "+") in g.vizinhos("(1,1)|-|{0}")


def test_fonte_energia_padrao_e_consumivel():
    linhas = [
        "#####",
        "#S*G#",
        "#####",
    ]
    # Modo padrao: '*' custa -2 toda vez e forma ciclo negativo
    g_padrao = construir_grafo_estados(linhas, incluir_alvo=True, fonte_consumivel=False)
    assert ("(1,2)|-|{}", -2, "L", "*") in g_padrao.vizinhos("(1,1)|-|{}")
    _, _, ciclo = bellman_ford(g_padrao, "(1,1)|-|{}")
    assert ciclo is not None

    # Modo --fonte-consumivel: '*' custa -2 na 1a vez e 1 depois (sem ciclo negativo)
    g_cons = construir_grafo_estados(linhas, incluir_alvo=True, fonte_consumivel=True)
    assert ("(1,2)|-|{0}", -2, "L", "*") in g_cons.vizinhos("(1,1)|-|{}")
    assert ("(1,2)|-|{0}", 1, "L", "*") in g_cons.vizinhos("(1,1)|-|{0}")
    dist, _, ciclo_cons = bellman_ford(g_cons, "(1,1)|-|{}")
    assert ciclo_cons is None
    assert dist[NO_ALVO] == -1


def test_ordem_dos_vizinhos_n_l_s_o_e_parada_em_g():
    linhas = [
        "#####",
        "#...#",
        "#.S.#",
        "#.G.#",
        "#####",
    ]
    g = construir_grafo_estados(linhas, incluir_alvo=False)
    movimentos = [mov for _, _, mov, _ in g.vizinhos("(2,2)|-|{}")]
    assert movimentos == ["N", "L", "S", "O"]
    # Estado em G nao tem arestas de saida para vizinhos da grade
    assert g.vizinhos("(3,2)|-|{}") == []


def test_custos_de_terreno_lama_e_agua():
    linhas = [
        "#####",
        "#S,~#",
        "#..G#",
        "#####",
    ]
    g = construir_grafo_estados(linhas, incluir_alvo=False)
    assert ("(1,2)|-|{}", 3, "L", ",") in g.vizinhos("(1,1)|-|{}")
    assert ("(1,3)|-|{}", 5, "L", "~") in g.vizinhos("(1,2)|-|{}")


def test_grafo_posicoes_variacoes_portas_e_bonus():
    # No MAPA_MINIMO_GRUPO, porta A em (1,3) separa S=(1,1) de G=(1,4)
    g_chao = construir_grafo_posicoes(MAPA_MINIMO_GRUPO, portas_como="chao")
    dist_chao, pai_chao, _ = bfs(g_chao, (1, 1))
    assert dist_chao[(1, 4)] == 3
    assert montar_caminho(pai_chao, (1, 4)) == [(1, 1), (1, 2), (1, 3), (1, 4)]

    g_parede = construir_grafo_posicoes(MAPA_MINIMO_GRUPO, portas_como="parede")
    dist_parede, _, _ = bfs(g_parede, (1, 1))
    assert (1, 4) not in dist_parede


def test_mapas_fornecidos_constroem_grafo_estados():
    pasta = Path(__file__).resolve().parents[1] / "data" / "mapas"
    linhas_m02 = ler_mapa(pasta / "m02_uma_chave.txt")
    g_m02 = construir_grafo_estados(linhas_m02, incluir_alvo=True)
    sub_m02 = grafo_estados_sem_alvo(g_m02)

    assert calcular_teto_teorico(linhas_m02) == 46
    assert sub_m02.ordem() == 39

    dist_bfs, _, _ = bfs(g_m02, "(1,1)|-|{}")
    # Passos reais no labirinto = distancia ate ALVO menos o arco virtual (custo 0)
    assert dist_bfs[NO_ALVO] - 1 == 34

    dist_dij, _, _ = dijkstra(g_m02, "(1,1)|-|{}")
    assert dist_dij[NO_ALVO] == 46
