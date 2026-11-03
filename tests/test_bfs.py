import random

import networkx as nx
import pytest

from src.graphs.graph import GrafoDirigido
from src.graphs.algorithms import bfs, montar_caminho


def grafo_exemplo():
    #   A -> B -> D -> E
    #   A -> C -> D
    #   D -> A  (ciclo)
    #   F -> A  (F nao e alcancavel a partir de A)
    g = GrafoDirigido("exemplo")
    g.adicionar_arco("A", "B")
    g.adicionar_arco("A", "C")
    g.adicionar_arco("B", "D")
    g.adicionar_arco("C", "D")
    g.adicionar_arco("D", "E")
    g.adicionar_arco("D", "A")
    g.adicionar_arco("F", "A")
    return g


def separar_niveis(dist):
    niveis = {}
    for no, d in dist.items():
        if d not in niveis:
            niveis[d] = set()
        niveis[d].add(no)
    return niveis


def test_niveis_corretos():
    dist, pai, ordem = bfs(grafo_exemplo(), "A")
    niveis = separar_niveis(dist)
    assert niveis[0] == {"A"}
    assert niveis[1] == {"B", "C"}
    assert niveis[2] == {"D"}
    assert niveis[3] == {"E"}


def test_no_inalcancavel_fica_fora():
    dist, pai, ordem = bfs(grafo_exemplo(), "A")
    assert "F" not in dist
    assert montar_caminho(pai, "F") is None


def test_ciclo_nao_trava_e_visita_cada_no_uma_vez():
    dist, pai, ordem = bfs(grafo_exemplo(), "A")
    assert ordem == ["A", "B", "C", "D", "E"]


def test_caminho_segue_ordem_dos_vizinhos():
    # D pode ser alcancado por B ou por C (mesmo tamanho)
    # como B foi inserido antes, o caminho tem que passar por B
    dist, pai, ordem = bfs(grafo_exemplo(), "A")
    assert montar_caminho(pai, "E") == ["A", "B", "D", "E"]
    assert montar_caminho(pai, "A") == ["A"]


def test_bfs_ignora_peso():
    g = GrafoDirigido()
    g.adicionar_arco("A", "B", 100)
    g.adicionar_arco("A", "C", 1)
    g.adicionar_arco("C", "B", 1)
    dist, pai, ordem = bfs(g, "A")
    assert dist["B"] == 1


def test_origem_inexistente_da_erro():
    with pytest.raises(KeyError):
        bfs(grafo_exemplo(), "Z")


def test_compara_com_networkx():
    random.seed(42)
    g = GrafoDirigido()
    g_nx = nx.DiGraph()
    for i in range(200):
        g.adicionar_no(i)
        g_nx.add_node(i)
    for _ in range(600):
        u = random.randint(0, 199)
        v = random.randint(0, 199)
        g.adicionar_arco(u, v)
        g_nx.add_edge(u, v)

    dist, pai, ordem = bfs(g, 0)
    esperado = nx.single_source_shortest_path_length(g_nx, 0)
    assert dist == esperado