import random

import networkx as nx
import pytest

from src.graphs.graph import GrafoDirigido
from src.graphs.algorithms import dfs


def grafo_exemplo():
    #   A -> B -> C
    #   C -> A        retorno (fecha ciclo A, B, C)
    #   A -> C        avanco (C ja foi terminado e e descendente de A)
    #   A -> D -> C   cruzamento (C ja terminou em outro galho)
    g = GrafoDirigido("exemplo")
    g.adicionar_arco("A", "B")
    g.adicionar_arco("A", "C")
    g.adicionar_arco("A", "D")
    g.adicionar_arco("B", "C")
    g.adicionar_arco("C", "A")
    g.adicionar_arco("D", "C")
    return g


def tipos(classificacao):
    resultado = {}
    for u, v, tipo in classificacao:
        resultado[(u, v)] = tipo
    return resultado


def test_classificacao_dos_arcos():
    pai, ordem, classificacao, tem_ciclo = dfs(grafo_exemplo(), "A")
    t = tipos(classificacao)
    assert t[("A", "B")] == "arvore"
    assert t[("B", "C")] == "arvore"
    assert t[("C", "A")] == "retorno"
    assert t[("A", "C")] == "avanco"
    assert t[("A", "D")] == "arvore"
    assert t[("D", "C")] == "cruzamento"


def test_detecta_ciclo():
    pai, ordem, classificacao, tem_ciclo = dfs(grafo_exemplo(), "A")
    assert tem_ciclo is True


def test_grafo_sem_ciclo():
    g = GrafoDirigido()
    g.adicionar_arco("A", "B")
    g.adicionar_arco("A", "C")
    g.adicionar_arco("B", "C")
    pai, ordem, classificacao, tem_ciclo = dfs(g, "A")
    assert tem_ciclo is False
    assert "retorno" not in [tipo for u, v, tipo in classificacao]


def test_ordem_segue_os_vizinhos():
    pai, ordem, classificacao, tem_ciclo = dfs(grafo_exemplo(), "A")
    assert ordem == ["A", "B", "C", "D"]
    assert pai == {"A": None, "B": "A", "C": "B", "D": "A"}


def test_so_visita_o_que_a_origem_alcanca():
    g = grafo_exemplo()
    g.adicionar_arco("X", "A")
    pai, ordem, classificacao, tem_ciclo = dfs(g, "A")
    assert "X" not in ordem


def test_sem_origem_visita_todos():
    g = grafo_exemplo()
    g.adicionar_arco("X", "A")
    pai, ordem, classificacao, tem_ciclo = dfs(g)
    assert set(ordem) == {"A", "B", "C", "D", "X"}
    assert tipos(classificacao)[("X", "A")] == "cruzamento"


def test_caminho_longo_nao_estoura_recursao():
    g = GrafoDirigido()
    for i in range(100000):
        g.adicionar_arco(i, i + 1)
    pai, ordem, classificacao, tem_ciclo = dfs(g, 0)
    assert len(ordem) == 100001


def test_origem_inexistente_da_erro():
    with pytest.raises(KeyError):
        dfs(grafo_exemplo(), "Z")


def test_ciclo_igual_ao_networkx():
    for semente in range(50):
        random.seed(semente)
        g = GrafoDirigido()
        g_nx = nx.DiGraph()
        for i in range(30):
            g.adicionar_no(i)
            g_nx.add_node(i)
        for _ in range(40):
            u = random.randint(0, 29)
            v = random.randint(0, 29)
            g.adicionar_arco(u, v)
            g_nx.add_edge(u, v)

        pai, ordem, classificacao, tem_ciclo = dfs(g)
        assert tem_ciclo == (not nx.is_directed_acyclic_graph(g_nx))
        assert len(classificacao) == g.tamanho()