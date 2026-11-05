SIMBOLOS = "#.SG,~abcdABCD><^v+*"


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
