import random

import networkx as nx
import pytest

from src.graphs.graph import GrafoDirigido
from src.graphs.algorithms import bfs, dijkstra, montar_caminho


def grafo_terreno():
    # parecido com o m01: o caminho com menos passos (S -> A -> G) passa pela agua
    # e sai mais caro que o caminho mais longo pelo chao
    #   S -> A (1), A -> G (5)          2 passos, custo 6
    #   S -> B (1), B -> C (1), C -> G (1)   3 passos, custo 3
    g = GrafoDirigido("terreno")
    g.adicionar_arco("S", "A", 1)
    g.adicionar_arco("S", "B", 1)
    g.adicionar_arco("A", "G", 5)
    g.adicionar_arco("B", "C", 1)
    g.adicionar_arco("C", "G", 1)
    g.adicionar_arco("X", "S", 1)
    return g


def test_caminho_mais_barato():
    dist, pai, ordem = dijkstra(grafo_terreno(), "S")
    assert dist["G"] == 3
    assert montar_caminho(pai, "G") == ["S", "B", "C", "G"]


def test_bfs_e_dijkstra_dao_caminhos_diferentes():
    g = grafo_terreno()
    dist_bfs, pai_bfs, _ = bfs(g, "S")
    dist_dij, pai_dij, _ = dijkstra(g, "S")
    assert montar_caminho(pai_bfs, "G") == ["S", "A", "G"]
    assert montar_caminho(pai_dij, "G") == ["S", "B", "C", "G"]


def test_no_inalcancavel_fica_fora():
    dist, pai, ordem = dijkstra(grafo_terreno(), "S")
    assert "X" not in dist
    assert montar_caminho(pai, "X") is None


def test_arco_de_peso_zero():
    g = grafo_terreno()
    g.adicionar_arco("G", "ALVO", 0)
    dist, pai, ordem = dijkstra(g, "S")
    assert dist["ALVO"] == 3


def test_recusa_peso_negativo():
    g = grafo_terreno()
    g.adicionar_arco("C", "B", -4)
    with pytest.raises(ValueError) as erro:
        dijkstra(g, "S")
    assert "C -> B" in str(erro.value)


def test_origem_inexistente_da_erro():
    with pytest.raises(KeyError):
        dijkstra(grafo_terreno(), "Z")


def test_compara_com_networkx():
    random.seed(42)
    g = GrafoDirigido()
    g_nx = nx.DiGraph()
    for i in range(200):
        g.adicionar_no(i)
        g_nx.add_node(i)
    for _ in range(800):
        u = random.randint(0, 199)
        v = random.randint(0, 199)
        peso = random.randint(0, 10)
        if g_nx.has_edge(u, v):
            continue
        g.adicionar_arco(u, v, peso)
        g_nx.add_edge(u, v, weight=peso)

    dist, pai, ordem = dijkstra(g, 0)
    esperado = nx.single_source_dijkstra_path_length(g_nx, 0)
    assert dist == esperado