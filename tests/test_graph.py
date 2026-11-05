import pytest

from src.graphs.graph import GrafoDirigido


def grafo_exemplo():
    # A -> B, A -> C, C -> B; D fica isolado.
    g = GrafoDirigido("exemplo")
    g.adicionar_arco("A", "B", 3, "L", ".")
    g.adicionar_arco("A", "C", 1, "S", "a")
    g.adicionar_arco("C", "B", -4, "O", "+")
    g.adicionar_no("D")
    return g


def test_grafo_vazio():
    g = GrafoDirigido()
    assert g.nos() == []
    assert g.metricas() == {"ordem": 0, "tamanho": 0, "densidade": 0.0}
    assert g.tabela_graus() == []
    assert g.tem_peso_neg is False


def test_no_isolado():
    g = GrafoDirigido()
    g.adicionar_no("A")
    assert g.tem_no("A")
    assert not g.tem_no("B")
    assert g.vizinhos("A") == []
    assert g.grau_entrada("A") == 0
    assert g.grau_saida("A") == 0
    assert g.metricas() == {"ordem": 1, "tamanho": 0, "densidade": 0.0}


def test_adicionar_no_existente_preserva_arcos():
    g = GrafoDirigido()
    g.adicionar_arco("A", "B", 3)
    g.adicionar_no("A")
    g.adicionar_no("B")
    assert g.nos() == ["A", "B"]
    assert g.vizinhos("A") == [("B", 3, "", "")]
    assert g.grau_entrada("B") == 1
    assert g.tamanho() == 1


def test_arco_cria_nos_sem_inverter_direcao():
    g = GrafoDirigido()
    g.adicionar_arco("A", "B")
    assert g.nos() == ["A", "B"]
    assert g.vizinhos("A") == [("B", 1, "", "")]
    assert g.vizinhos("B") == []
    assert g.tem_peso_neg is False


def test_arcos_preservam_peso_dados_e_ordem():
    g = grafo_exemplo()
    assert g.vizinhos("A") == [("B", 3, "L", "."), ("C", 1, "S", "a")]
    assert g.vizinhos("C") == [("B", -4, "O", "+")]
    assert g.tem_peso_neg is True


def test_graus_e_metricas():
    g = grafo_exemplo()
    assert g.grau_entrada("B") == 2
    assert g.grau_saida("A") == 2
    assert g.tabela_graus() == [("A", 0, 2), ("B", 2, 0), ("C", 1, 1), ("D", 0, 0)]
    assert g.metricas() == {"ordem": 4, "tamanho": 3, "densidade": 0.25}


def test_no_inexistente_da_erro():
    g = grafo_exemplo()
    with pytest.raises(KeyError, match="Z"):
        g.vizinhos("Z")
    with pytest.raises(KeyError, match="Z"):
        g.grau_entrada("Z")
    with pytest.raises(KeyError, match="Z"):
        g.grau_saida("Z")


def test_transposto_inverte_arcos_e_preserva_dados():
    g = grafo_exemplo()
    inv = g.transposto()
    assert inv.nos() == ["A", "B", "C", "D"]
    assert inv.vizinhos("A") == []
    assert inv.vizinhos("B") == [("A", 3, "L", "."), ("C", -4, "O", "+")]
    assert inv.vizinhos("C") == [("A", 1, "S", "a")]
    assert inv.vizinhos("D") == []
    assert inv.tamanho() == 3
    assert inv.grau_entrada("A") == 2
    assert inv.grau_saida("B") == 2
    assert inv.tem_peso_neg is True


def test_subgrafo_mantem_apenas_nos_e_arcos_selecionados():
    g = grafo_exemplo()
    sub = g.subgrafo_induzido(["D", "B", "A"])
    # A ordem original dos nos e preservada, mesmo com a selecao invertida.
    assert sub.nos() == ["A", "B", "D"]
    assert sub.vizinhos("A") == [("B", 3, "L", ".")]
    assert sub.vizinhos("B") == []
    assert sub.vizinhos("D") == []
    assert sub.tamanho() == 1
    assert sub.grau_entrada("B") == 1
    assert sub.grau_saida("A") == 1
    assert sub.tem_peso_neg is False


def test_subgrafo_preserva_arco_negativo():
    sub = grafo_exemplo().subgrafo_induzido(["B", "C"])
    assert sub.nos() == ["B", "C"]
    assert sub.vizinhos("C") == [("B", -4, "O", "+")]
    assert sub.tamanho() == 1
    assert sub.tem_peso_neg is True


def test_selecao_vazia_produz_subgrafo_vazio():
    sub = grafo_exemplo().subgrafo_induzido([])
    assert sub.nos() == []
    assert sub.metricas() == {"ordem": 0, "tamanho": 0, "densidade": 0.0}


def test_transposto_e_subgrafo_nao_alteram_original():
    g = grafo_exemplo()
    inv = g.transposto()
    sub = g.subgrafo_induzido(["A", "B", "D"])

    assert g.nos() == ["A", "B", "C", "D"]
    assert g.vizinhos("A") == [("B", 3, "L", "."), ("C", 1, "S", "a")]
    assert g.vizinhos("B") == []
    assert g.vizinhos("C") == [("B", -4, "O", "+")]
    assert g.vizinhos("D") == []
    assert g.tabela_graus() == [("A", 0, 2), ("B", 2, 0), ("C", 1, 1), ("D", 0, 0)]
    assert g.tem_peso_neg is True

    # Alterar as copias tambem nao pode mudar o original.
    inv.adicionar_arco("A", "D", 2)
    sub.adicionar_arco("B", "D", 2)
    assert g.grau_entrada("D") == 0
    assert g.grau_saida("A") == 2
    assert g.grau_saida("B") == 0
    assert g.tamanho() == 3
