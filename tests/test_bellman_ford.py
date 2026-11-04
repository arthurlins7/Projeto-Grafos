import random

import networkx as nx
import pytest

from src.graphs.graph import GrafoDirigido
from src.graphs.algorithms import bellman_ford, montar_caminho, custo_caminho


def grafo_bonus():
    # parecido com o m05: tem peso negativo, mas nao tem ciclo negativo
    #   S -> A (1), A -> G (1)              custo 2
    #   S -> B (1), B -> C (-4), C -> G (1)  custo -2
    g = GrafoDirigido("bonus")
    g.adicionar_arco("S", "A", 1)
    g.adicionar_arco("S", "B", 1)
    g.adicionar_arco("A", "G", 1)
    g.adicionar_arco("B", "C", -4)
    g.adicionar_arco("C", "G", 1)
    return g


def grafo_fonte():
    # parecido com o m06: A -> B -> A custa -2 + -2, da pra dar volta infinita
    g = GrafoDirigido("fonte")
    g.adicionar_arco("S", "A", 1)
    g.adicionar_arco("A", "B", -2)
    g.adicionar_arco("B", "A", -2)
    g.adicionar_arco("B", "G", 1)
    return g


def test_peso_negativo_sem_ciclo():
    dist, pai, ciclo = bellman_ford(grafo_bonus(), "S")
    assert ciclo is None
    assert dist == {"S": 0, "A": 1, "B": 1, "C": -3, "G": -2}
    assert montar_caminho(pai, "G") == ["S", "B", "C", "G"]


def test_ciclo_negativo_e_retornado():
    g = grafo_fonte()
    dist, pai, ciclo = bellman_ford(g, "S")
    assert ciclo is not None
    assert ciclo[0] == ciclo[-1]
    assert set(ciclo) == {"A", "B"}
    assert custo_caminho(g, ciclo) == -4


def test_laco_negativo():
    g = GrafoDirigido()
    g.adicionar_arco("S", "A", 1)
    g.adicionar_arco("A", "A", -1)
    dist, pai, ciclo = bellman_ford(g, "S")
    assert ciclo == ["A", "A"]


def test_ciclo_negativo_inalcancavel_nao_conta():
    g = grafo_bonus()
    g.adicionar_arco("X", "Y", -5)
    g.adicionar_arco("Y", "X", -5)
    dist, pai, ciclo = bellman_ford(g, "S")
    assert ciclo is None
    assert "X" not in dist


def test_ciclo_positivo_nao_e_ciclo_negativo():
    g = GrafoDirigido()
    g.adicionar_arco("S", "A", 1)
    g.adicionar_arco("A", "B", 2)
    g.adicionar_arco("B", "A", 2)
    dist, pai, ciclo = bellman_ford(g, "S")
    assert ciclo is None
    assert dist == {"S": 0, "A": 1, "B": 3}


def test_origem_inexistente_da_erro():
    with pytest.raises(KeyError):
        bellman_ford(grafo_bonus(), "Z")


def test_compara_com_networkx_sem_ciclo():
    # so arcos de i para j com i < j, entao nao tem ciclo nenhum
    random.seed(42)
    g = GrafoDirigido()
    g_nx = nx.DiGraph()
    for i in range(150):
        g.adicionar_no(i)
        g_nx.add_node(i)
    for _ in range(600):
        u = random.randint(0, 148)
        v = random.randint(u + 1, 149)
        peso = random.randint(-5, 10)
        if g_nx.has_edge(u, v):
            continue
        g.adicionar_arco(u, v, peso)
        g_nx.add_edge(u, v, weight=peso)

    dist, pai, ciclo = bellman_ford(g, 0)
    esperado = nx.single_source_bellman_ford_path_length(g_nx, 0)
    assert ciclo is None
    assert dist == esperado


def test_detecta_ciclo_igual_ao_networkx():
    for semente in range(50):
        random.seed(semente)
        g = GrafoDirigido()
        g_nx = nx.DiGraph()
        for i in range(30):
            g.adicionar_no(i)
            g_nx.add_node(i)
        for _ in range(80):
            u = random.randint(0, 29)
            v = random.randint(0, 29)
            peso = random.randint(-3, 10)
            if g_nx.has_edge(u, v):
                continue
            g.adicionar_arco(u, v, peso)
            g_nx.add_edge(u, v, weight=peso)

        dist, pai, ciclo = bellman_ford(g, 0)
        alcancaveis = nx.descendants(g_nx, 0) | {0}
        tem_ciclo = nx.negative_edge_cycle(g_nx.subgraph(alcancaveis).copy())

        assert (ciclo is not None) == tem_ciclo
        if ciclo is not None:
            assert custo_caminho(g, ciclo) < 0