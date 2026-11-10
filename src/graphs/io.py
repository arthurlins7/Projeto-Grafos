import pandas as pd

from src.graphs.graph import GrafoDirigido


SIMBOLOS = "#.SG,~abcdABCD><^v+*"
COLUNAS_DATASET = ["origem", "destino", "sinal"]


def ler_mapa(caminho):
    """Le o arquivo e devolve as linhas do mapa validado."""
    with open(caminho, encoding="utf-8-sig") as arquivo:
        linhas = [linha.rstrip("\n") for linha in arquivo if not linha.startswith(";")]

    validar_mapa(linhas)
    return linhas


def validar_mapa(linhas):
    """Confere o formato e os simbolos, sem buscar uma solucao."""
    if not linhas:
        raise ValueError("O mapa nao pode estar vazio.")

    largura = len(linhas[0])
    inicios = 0
    saidas = 0

    for numero, linha in enumerate(linhas, start=1):
        if not linha:
            raise ValueError(f"A linha {numero} do mapa esta vazia.")
        if len(linha) != largura:
            raise ValueError(
                f"A linha {numero} tem {len(linha)} colunas; esperado: {largura}."
            )

        for coluna, simbolo in enumerate(linha, start=1):
            if simbolo not in SIMBOLOS:
                raise ValueError(
                    f"Simbolo desconhecido {simbolo!r} na linha {numero}, coluna {coluna}."
                )

        inicios += linha.count("S")
        saidas += linha.count("G")

    if inicios != 1:
        raise ValueError(f"O mapa deve ter exatamente um S; encontrados: {inicios}.")
    if saidas == 0:
        raise ValueError("O mapa deve ter pelo menos um G.")


def localizar_inicio_e_saidas(linhas):
    """Devolve inicio e saidas como (linha, coluna), contando a partir de zero."""
    validar_mapa(linhas)
    inicio = None
    saidas = []

    for linha, conteudo in enumerate(linhas):
        for coluna, simbolo in enumerate(conteudo):
            if simbolo == "S":
                inicio = (linha, coluna)
            elif simbolo == "G":
                saidas.append((linha, coluna))

    return inicio, saidas


def ler_dataset(caminho):
    """Le a tabela de relacoes e valida seus dados."""
    try:
        # [IA] Claude - sintaxe do pd.read_csv (sep, comment, header)
        dados = pd.read_csv(caminho, sep="\t", comment="#", header=None, encoding="utf-8-sig")
    except pd.errors.EmptyDataError as erro:
        raise ValueError("O dataset nao pode estar vazio.") from erro
    except pd.errors.ParserError as erro:
        raise ValueError("O dataset deve ter tres colunas separadas por TAB.") from erro
    except UnicodeError as erro:
        raise ValueError("O dataset deve estar em UTF-8.") from erro

    if dados.shape[1] != 3:
        raise ValueError("O dataset deve ter tres colunas: origem, destino e sinal.")

    dados.columns = COLUNAS_DATASET
    validar_dataset(dados)
    return dados


def validar_dataset(dados):
    """Confere as colunas, os identificadores e os sinais das relacoes."""
    if list(dados.columns) != COLUNAS_DATASET:
        raise ValueError("O dataset deve ter as colunas origem, destino e sinal, nessa ordem.")
    if dados.empty:
        raise ValueError("O dataset nao pode estar vazio.")
    if dados.isna().any().any():
        raise ValueError("O dataset nao pode conter valores vazios.")

    for coluna in COLUNAS_DATASET:
        if not pd.api.types.is_integer_dtype(dados[coluna].dtype):
            raise ValueError(f"A coluna {coluna} deve conter apenas numeros inteiros.")

    if not dados["sinal"].isin([1, -1]).all():
        raise ValueError("O sinal de cada relacao deve ser 1 ou -1.")


def montar_grafo_dataset(dados):
    """Monta o grafo dirigido, usando o sinal como peso de cada arco."""
    validar_dataset(dados)
    grafo = GrafoDirigido("Slashdot")

    for origem, destino, sinal in dados.itertuples(index=False, name=None):
        grafo.adicionar_arco(origem, destino, peso=sinal)

    return grafo