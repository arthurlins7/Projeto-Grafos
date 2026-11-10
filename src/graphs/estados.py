from src.graphs.graph import GrafoDirigido
from src.graphs.io import localizar_inicio_e_saidas, validar_mapa


NO_ALVO = "ALVO"

# Ordem obrigatoria dos movimentos: Norte, Leste, Sul, Oeste.
MOVIMENTOS = [
    ("N", -1, 0),
    ("L", 0, 1),
    ("S", 1, 0),
    ("O", 0, -1),
]

DIRECAO_ESTEIRA = {
    "^": "N",
    ">": "L",
    "v": "S",
    "<": "O",
}

CUSTO_TERRENO = {
    ".": 1,
    "S": 1,
    "G": 1,
    ",": 3,
    "~": 5,
    "*": -2,
}


def formatar_estado(linha, coluna, chaves=frozenset(), bonus=frozenset()):
    """Formata o rotulo obrigatorio: (linha,coluna)|chaves|{bonus}."""
    txt_chaves = "".join(sorted(chaves)) if chaves else "-"
    if bonus:
        txt_bonus = "{" + ",".join(str(i) for i in sorted(bonus)) + "}"
    else:
        txt_bonus = "{}"
    return f"({linha},{coluna})|{txt_chaves}|{txt_bonus}"


def decompor_estado(rotulo):
    """Extrai ((linha, coluna), chaves_str, bonus_tuple) de um rotulo de estado."""
    if rotulo == NO_ALVO:
        raise ValueError("O no ALVO nao possui coordenadas nem camada.")
    pos_txt, chaves_txt, bonus_txt = rotulo.split("|")
    lin_txt, col_txt = pos_txt[1:-1].split(",")
    conteudo_bonus = bonus_txt[1:-1]
    if conteudo_bonus:
        bonus = tuple(int(x) for x in conteudo_bonus.split(","))
    else:
        bonus = ()
    return (int(lin_txt), int(col_txt)), chaves_txt, bonus


def indexar_bonus(linhas, fonte_consumivel=False):
    """Numera os bonus '+' (e '*' se fonte_consumivel=True) de 0 em diante em ordem de leitura."""
    indices = {}
    proximo = 0
    simbolos_consumiveis = "+*" if fonte_consumivel else "+"
    for lin, linha in enumerate(linhas):
        for col, simbolo in enumerate(linha):
            if simbolo in simbolos_consumiveis:
                indices[(lin, col)] = proximo
                proximo += 1
    return indices


def calcular_teto_teorico(linhas):
    """Calcula casas_livres * 2^(n_chaves) * 2^(n_bonus)."""
    validar_mapa(linhas)
    casas_livres = 0
    chaves = set()
    num_bonus = 0

    for linha in linhas:
        for simbolo in linha:
            if simbolo != "#":
                casas_livres += 1
            if simbolo in "abcd":
                chaves.add(simbolo)
            elif simbolo == "+":
                num_bonus += 1

    return casas_livres * (2 ** len(chaves)) * (2 ** num_bonus)


def _movimentos_permitidos(simbolo_atual):
    """Devolve a lista de movimentos (direcao, dlin, dcol) a partir da casa atual."""
    if simbolo_atual == "G":
        return []
    if simbolo_atual in DIRECAO_ESTEIRA:
        direcao_unica = DIRECAO_ESTEIRA[simbolo_atual]
        return [m for m in MOVIMENTOS if m[0] == direcao_unica]
    return MOVIMENTOS


def _custo_casa_posicoes(simbolo, bonus_fixo=True):
    """Custo de entrar na casa no modelo ingenuo (grafo de posicoes)."""
    if simbolo in CUSTO_TERRENO:
        return CUSTO_TERRENO[simbolo]
    if simbolo in "abcdABCD><^v":
        return 1
    if simbolo == "+":
        return -4 if bonus_fixo else 1
    raise ValueError(f"Simbolo invalido para custo: {simbolo!r}")


def construir_grafo_posicoes(linhas, portas_como="chao", bonus_fixo=True, nome="G_pos"):
    """Constroi o grafo de posicoes (G_pos) do mapa.

    portas_como: 'chao' (portas A-D transitaveis com custo 1)
                 ou 'parede' (portas A-D bloqueadas como parede).
    bonus_fixo: se True, '+' vale -4 fixo; se False, vale 1.
    """
    validar_mapa(linhas)
    if portas_como not in ("chao", "parede"):
        raise ValueError("portas_como deve ser 'chao' ou 'parede'.")

    altura = len(linhas)
    largura = len(linhas[0])
    grafo = GrafoDirigido(nome=nome)

    bloqueados = {"#"}
    if portas_como == "parede":
        bloqueados.update("ABCD")

    for lin in range(altura):
        for col in range(largura):
            simbolo = linhas[lin][col]
            if simbolo in bloqueados:
                continue
            origem = (lin, col)
            grafo.adicionar_no(origem)

            for direcao, dlin, dcol in _movimentos_permitidos(simbolo):
                nlin = lin + dlin
                ncol = col + dcol
                if not (0 <= nlin < altura and 0 <= ncol < largura):
                    continue
                simbolo_dest = linhas[nlin][ncol]
                if simbolo_dest in bloqueados:
                    continue
                peso = _custo_casa_posicoes(simbolo_dest, bonus_fixo=bonus_fixo)
                grafo.adicionar_arco(
                    origem, (nlin, ncol), peso=peso, movimento=direcao, casa=simbolo_dest
                )

    return grafo


def construir_grafo_estados(
    linhas, incluir_alvo=True, fonte_consumivel=False, nome="G_est"
):
    """Constroi o grafo de estados (G_est) por exploracao BFS a partir do estado inicial."""
    inicio, _ = localizar_inicio_e_saidas(linhas)
    altura = len(linhas)
    largura = len(linhas[0])
    mapa_bonus = indexar_bonus(linhas, fonte_consumivel=fonte_consumivel)

    grafo = GrafoDirigido(nome=nome)
    lin_s, col_s = inicio
    estado_inicial = (lin_s, col_s, frozenset(), frozenset())
    rotulo_inicial = formatar_estado(lin_s, col_s)
    grafo.adicionar_no(rotulo_inicial)

    if incluir_alvo:
        grafo.adicionar_no(NO_ALVO)

    fila = [estado_inicial]
    visitados = {estado_inicial}
    ponteiro = 0

    while ponteiro < len(fila):
        lin, col, chaves, bonus = fila[ponteiro]
        ponteiro += 1

        simbolo_atual = linhas[lin][col]
        rotulo_atual = formatar_estado(lin, col, chaves, bonus)

        if simbolo_atual == "G":
            if incluir_alvo:
                grafo.adicionar_arco(rotulo_atual, NO_ALVO, peso=0, movimento="", casa="G")
            continue

        for direcao, dlin, dcol in _movimentos_permitidos(simbolo_atual):
            nlin = lin + dlin
            ncol = col + dcol
            if not (0 <= nlin < altura and 0 <= ncol < largura):
                continue

            simbolo_dest = linhas[nlin][ncol]
            if simbolo_dest == "#":
                continue

            # Porta: so entra quem possui a chave minuscula correspondente
            if simbolo_dest in "ABCD" and simbolo_dest.lower() not in chaves:
                continue

            novas_chaves = chaves
            novos_bonus = bonus

            if simbolo_dest in "abcd":
                novas_chaves = chaves | {simbolo_dest}
                peso = 1
            elif simbolo_dest in "ABCD" or simbolo_dest in "><^v":
                peso = 1
            elif simbolo_dest == "+":
                idx_b = mapa_bonus[(nlin, ncol)]
                if idx_b not in bonus:
                    peso = -4
                    novos_bonus = bonus | {idx_b}
                else:
                    peso = 1
            elif simbolo_dest == "*":
                if fonte_consumivel:
                    idx_f = mapa_bonus[(nlin, ncol)]
                    if idx_f not in bonus:
                        peso = -2
                        novos_bonus = bonus | {idx_f}
                    else:
                        peso = 1
                else:
                    peso = -2
            else:
                peso = CUSTO_TERRENO[simbolo_dest]

            prox_estado = (nlin, ncol, novas_chaves, novos_bonus)
            rotulo_prox = formatar_estado(nlin, ncol, novas_chaves, novos_bonus)
            grafo.adicionar_arco(
                rotulo_atual,
                rotulo_prox,
                peso=peso,
                movimento=direcao,
                casa=simbolo_dest,
            )

            if prox_estado not in visitados:
                visitados.add(prox_estado)
                fila.append(prox_estado)

    return grafo


def grafo_estados_sem_alvo(grafo):
    """Devolve o subgrafo induzido sem o no virtual ALVO (para metricas da Secao 3)."""
    if not grafo.tem_no(NO_ALVO):
        return grafo
    nos_reais = [no for no in grafo.nos() if no != NO_ALVO]
    sub = grafo.subgrafo_induzido(nos_reais)
    sub.nome = grafo.nome
    return sub
