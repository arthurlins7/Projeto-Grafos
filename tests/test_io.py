from pathlib import Path

import pytest

from src.graphs.estados import construir_grafo_estados
from src.graphs.io import (
    ler_dataset,
    ler_mapa,
    localizar_inicio_e_saidas,
    montar_grafo_dataset,
    salvar_arestas_csv,
    salvar_graus_csv,
    validar_mapa,
)


@pytest.mark.parametrize("linhas", [
    ["SG"],
    ["SGG"],
    ["S#G"],
    ["SAG"],
    ["S#.,~abcdABCD><^v+*G"],
])
def test_mapa_valido(linhas):
    assert validar_mapa(linhas) is None


def test_validacao_nao_altera_linhas():
    linhas = ["S.a", "A+G"]
    validar_mapa(linhas)
    assert linhas == ["S.a", "A+G"]


@pytest.mark.parametrize("linhas, mensagem", [
    ([], "mapa nao pode estar vazio"),
    ([""], "linha 1 do mapa esta vazia"),
    (["SG", ""], "linha 2 do mapa esta vazia"),
    (["SG", "..."], "linha 2 tem 3 colunas; esperado: 2"),
    (["..G"], "exatamente um S; encontrados: 0"),
    (["SSG"], "exatamente um S; encontrados: 2"),
    (["S.."], "pelo menos um G"),
    (["SXG"], "Simbolo desconhecido 'X' na linha 1, coluna 2"),
    (["S.G", ".?G"], "Simbolo desconhecido '\\?' na linha 2, coluna 2"),
    (["S G"], "Simbolo desconhecido ' ' na linha 1, coluna 2"),
    (["S;G"], "Simbolo desconhecido ';' na linha 1, coluna 2"),
])
def test_mapa_invalido(linhas, mensagem):
    with pytest.raises(ValueError, match=mensagem):
        validar_mapa(linhas)


@pytest.mark.parametrize("codificacao", ["utf-8", "utf-8-sig"])
@pytest.mark.parametrize("quebra", ["\n", "\r\n"])
def test_leitura_com_comentarios_e_quebras_de_linha(tmp_path, codificacao, quebra):
    caminho = tmp_path / "mapa.txt"
    conteudo = quebra.join(["; descricao do mapa", "S.a", ".AG", "; fim", ""])
    caminho.write_bytes(conteudo.encode(codificacao))
    assert ler_mapa(caminho) == ["S.a", ".AG"]


def test_leitura_sem_quebra_no_fim(tmp_path):
    caminho = tmp_path / "mapa.txt"
    caminho.write_text("SG", encoding="utf-8")
    assert ler_mapa(str(caminho)) == ["SG"]


@pytest.mark.parametrize("conteudo", ["", "; apenas comentario\n"])
def test_arquivo_sem_mapa(tmp_path, conteudo):
    caminho = tmp_path / "mapa.txt"
    caminho.write_text(conteudo, encoding="utf-8")
    with pytest.raises(ValueError, match="mapa nao pode estar vazio"):
        ler_mapa(caminho)


@pytest.mark.parametrize("conteudo", [" SG\n", "SG \n", "S\tG\n"])
def test_leitura_nao_remove_espacos_ou_tabs(tmp_path, conteudo):
    caminho = tmp_path / "mapa.txt"
    caminho.write_text(conteudo, encoding="utf-8")
    with pytest.raises(ValueError, match="Simbolo desconhecido"):
        ler_mapa(caminho)


def test_leitura_nao_ignora_linha_vazia(tmp_path):
    caminho = tmp_path / "mapa.txt"
    caminho.write_text("SG\n\n", encoding="utf-8")
    with pytest.raises(ValueError, match="linha 2 do mapa esta vazia"):
        ler_mapa(caminho)


def test_comentario_precisa_comecar_na_primeira_coluna(tmp_path):
    caminho = tmp_path / "mapa.txt"
    caminho.write_text(" ;\nSG\n", encoding="utf-8")
    with pytest.raises(ValueError, match="Simbolo desconhecido ' '"):
        ler_mapa(caminho)


def test_arquivo_inexistente(tmp_path):
    with pytest.raises(FileNotFoundError):
        ler_mapa(tmp_path / "inexistente.txt")


def test_arquivo_com_codificacao_invalida(tmp_path):
    caminho = tmp_path / "mapa.txt"
    caminho.write_bytes(b"S\xffG")
    with pytest.raises(UnicodeDecodeError):
        ler_mapa(caminho)


@pytest.mark.parametrize("linhas, inicio, saidas", [
    (["#######", "#S...G#", "#######"], (1, 1), [(1, 5)]),
    (["....", "...G", "S..."], (2, 0), [(1, 3)]),
    (["SG"], (0, 0), [(0, 1)]),
    (["S", "G"], (0, 0), [(1, 0)]),
    (["G..G", ".S..", "..G."], (1, 1), [(0, 0), (0, 3), (2, 2)]),
])
def test_localiza_inicio_e_saidas(linhas, inicio, saidas):
    assert localizar_inicio_e_saidas(linhas) == (inicio, saidas)


@pytest.mark.parametrize("linhas", [[], ["..G"], ["SSG"], ["S.."]])
def test_localizacao_recusa_mapa_invalido(linhas):
    with pytest.raises(ValueError):
        localizar_inicio_e_saidas(linhas)


def test_localizacao_nao_altera_mapa():
    linhas = ["S.G", "..G"]
    localizar_inicio_e_saidas(linhas)
    assert linhas == ["S.G", "..G"]


def test_localizacao_apos_leitura_nao_conta_comentarios(tmp_path):
    caminho = tmp_path / "mapa.txt"
    caminho.write_text("; comentario\nS..\n; outro comentario\n..G\n", encoding="utf-8")
    linhas = ler_mapa(caminho)
    assert localizar_inicio_e_saidas(linhas) == ((0, 0), [(1, 2)])


@pytest.mark.parametrize("nome, altura, largura", [
    ("m01_terreno.txt", 5, 13),
    ("m02_uma_chave.txt", 5, 13),
    ("m03_tres_chaves.txt", 10, 17),
    ("m04_esteiras.txt", 5, 13),
    ("m05_bonus.txt", 7, 15),
    ("m06_fonte.txt", 5, 13),
    ("m07_impossivel.txt", 6, 13),
    ("m08_grande.txt", 31, 71),
])
def test_mapas_fornecidos(nome, altura, largura):
    pasta = Path(__file__).resolve().parents[1] / "data" / "mapas"
    linhas = ler_mapa(pasta / nome)
    assert len(linhas) == altura
    assert all(len(linha) == largura for linha in linhas)
    inicio, saidas = localizar_inicio_e_saidas(linhas)
    assert inicio == (1, 1)
    assert len(saidas) == 1
    linha, coluna = saidas[0]
    assert linhas[linha][coluna] == "G"


def test_salvar_arestas_e_graus_csv_ignora_alvo(tmp_path):
    linhas = [
        "####",
        "#SG#",
        "####",
    ]
    g = construir_grafo_estados(linhas, incluir_alvo=True)
    arq_arestas = tmp_path / "arestas_teste.csv"
    arq_graus = tmp_path / "graus_teste.csv"

    salvar_arestas_csv(g, arq_arestas)
    salvar_graus_csv(g, arq_graus)

    conteudo_arestas = arq_arestas.read_text(encoding="utf-8").splitlines()
    assert conteudo_arestas == [
        "origem,destino,movimento,casa_destino,peso",
        '"(1,1)|-|{}","(1,2)|-|{}",L,G,1',
    ]

    conteudo_graus = arq_graus.read_text(encoding="utf-8").splitlines()
    assert conteudo_graus == [
        "estado,grau_entrada,grau_saida",
        '"(1,1)|-|{}",0,1',
        '"(1,2)|-|{}",1,0',
    ]


def test_ler_e_montar_dataset_valido(tmp_path):
    arq = tmp_path / "rede.txt"
    arq.write_text("# comentario\n0\t1\t1\n1\t2\t-1\n", encoding="utf-8")
    dados = ler_dataset(arq)
    g = montar_grafo_dataset(dados)
    assert g.ordem() == 3
    assert g.tamanho() == 2
    assert g.tem_peso_neg is True

