# [IA] Claude – codigo de desenho com matplotlib (arquivo inteiro)
import matplotlib.pyplot as plt
from matplotlib.colors import to_rgb
from matplotlib.patches import Patch



# CONFIGURACAO VISUAL  


# Os 8 primeiros sao as cores da Figura 1 do enunciado.

CORES = {
    "#": "#3a3a3a",        # parede
    ".": "#ffffff",        # chao
    ",": "#c9a26b",        # lama
    "~": "#80b1d3",        # agua
    "chave": "#fff2a8",    # a, b, c, d
    "porta": "#b39ddb",    # A, B, C, D
    "S": "#7fc97f",        # inicio
    "G": "#fdc086",        # saida
    "esteira": "#5d3a1a",  # > < ^ v  (marrom-escuro)
    "+": "#1b7f2e",        # bonus    (verde forte)
    "*": "#000000",        # fonte    (preta)
}

COR_GRADE = "#9e9e9e"      # linhas entre as casas
MOSTRAR_EIXOS = True       # numeros de linha/coluna nos eixos

# Texto de cada item da legenda, na ordem em que aparece.
# So entram na legenda os simbolos que existem no mapa desenhado.
LEGENDA = [
    ("#", "# parede"),
    (".", ". chão (1)"),
    (",", ", lama (3)"),
    ("~", "~ água (5)"),
    ("chave", "a–d chave (1)"),
    ("porta", "A–D porta (1)"),
    ("S", "S início (1)"),
    ("G", "G saída (1)"),
    ("esteira", "><^v esteira (1)"),
    ("+", "+ bônus (−4, depois 1)"),
    ("*", "* fonte (−2)"),
]


# ----------------------------------------------------------------------------
# Funcoes
# ----------------------------------------------------------------------------

def tipo_da_casa(simbolo):
    """Agrupa os simbolos que tem a mesma cor (chaves, portas e esteiras)."""
    if simbolo in "abcd":
        return "chave"
    if simbolo in "ABCD":
        return "porta"
    if simbolo in "><^v":
        return "esteira"
    return simbolo


def _cor_do_texto(cor_fundo):
    """Letra branca em casa escura e preta em casa clara."""
    r, g, b = to_rgb(cor_fundo)
    luminancia = 0.299 * r + 0.587 * g + 0.114 * b
    return "white" if luminancia < 0.5 else "black"


# [IA] Claude – codigo de desenho do mapa (matplotlib)
def desenhar_mapa(linhas, titulo, ax=None):
    """Desenha a grade do mapa com uma cor por simbolo, titulo e legenda.

    linhas: lista de strings do mapa (o retorno de ler_mapa, de io.py).
    titulo: texto do titulo (o grupo usa o nome do arquivo do mapa).
    ax: eixo do matplotlib onde desenhar; se for None, cria uma figura nova.

    Devolve (fig, ax), para que outras funcoes desenhem por cima
    (percurso, heatmap etc.).
    """
    altura = len(linhas)
    largura = len(linhas[0])

    if ax is None:
        lado = min(0.55, 16 / largura)  # polegadas por casa
        fig, ax = plt.subplots(figsize=(largura * lado + 1.2, altura * lado + 1.8))
    else:
        fig = ax.figure

    # Imagem RGB: um pixel por casa, linha 0 no topo (igual ao rotulo (linha, coluna)).
    imagem = [[to_rgb(CORES[tipo_da_casa(s)]) for s in linha] for linha in linhas]
    ax.imshow(imagem, interpolation="nearest")

    # Linhas da grade entre as casas.
    ax.set_xticks([x - 0.5 for x in range(largura + 1)], minor=True)
    ax.set_yticks([y - 0.5 for y in range(altura + 1)], minor=True)
    ax.grid(which="minor", color=COR_GRADE, linewidth=0.6)
    ax.tick_params(which="minor", length=0)

    # Tamanho da letra proporcional ao tamanho da casa na figura.
    fig.canvas.draw()
    largura_eixo_pol = ax.get_window_extent().width / fig.dpi
    tamanho_letra = max(5, 0.42 * 72 * largura_eixo_pol / largura)

    # Simbolo escrito dentro da casa (parede e chao ficam sem texto, como na Figura 1).
    for lin, linha in enumerate(linhas):
        for col, simbolo in enumerate(linha):
            if simbolo in "#.":
                continue
            ax.text(
                col, lin, simbolo,
                ha="center", va="center",
                fontsize=tamanho_letra, fontfamily="monospace", fontweight="bold",
                color=_cor_do_texto(CORES[tipo_da_casa(simbolo)]),
            )

    # Eixos (rotulos de linha e coluna).
    if MOSTRAR_EIXOS:
        passo = 1 if largura <= 20 else 5
        ax.set_xticks(range(0, largura, passo))
        ax.set_yticks(range(0, altura, 1 if altura <= 20 else 5))
        ax.set_xlabel("coluna")
        ax.set_ylabel("linha")
        ax.tick_params(which="major", length=0, labelsize=8)
    else:
        ax.set_xticks([])
        ax.set_yticks([])
    for borda in ax.spines.values():
        borda.set_visible(False)

    ax.set_title(titulo)

    # Legenda so com os tipos de casa presentes no mapa.
    presentes = {tipo_da_casa(s) for linha in linhas for s in linha}
    itens = [
        Patch(facecolor=CORES[tipo], edgecolor=COR_GRADE, label=texto)
        for tipo, texto in LEGENDA
        if tipo in presentes
    ]
    ax.legend(
        handles=itens,
        loc="upper center",
        bbox_to_anchor=(0.5, 0),
        borderaxespad=3.2 if MOSTRAR_EIXOS else 1.0,
        ncol=min(4, len(itens)),
        frameon=False,
    )

    return fig, ax


def salvar_figura(fig, caminho):
    """Salva a figura em PNG e libera a memoria."""
    fig.savefig(caminho, dpi=150, bbox_inches="tight")
    plt.close(fig)


# ----------------------------------------------------------------------------
# Figuras da Secao 8
# [IA] Claude - funcoes de desenho das figuras (matplotlib), revisadas pelo grupo
# ----------------------------------------------------------------------------

CORES_CAMADA = ["#1f77b4", "#d62728", "#2ca02c", "#9467bd", "#ff7f0e", "#8c564b"]


def desenhar_percurso(linhas, percurso, titulo):
    """Desenha o caminho por cima do mapa; a cor muda a cada chave coletada.

    percurso: lista de passos do percurso_<mapa>.json (cada um com linha, coluna e chaves).
    """
    fig, ax = desenhar_mapa(linhas, titulo)
    legenda_mapa = ax.get_legend()

    # separa o caminho em trechos com o mesmo conjunto de chaves
    trechos = []
    for passo in percurso:
        if not trechos or trechos[-1][0] != passo["chaves"]:
            trechos.append((passo["chaves"], []))
            if len(trechos) > 1:
                # o trecho novo comeca na casa onde a chave foi pega
                trechos[-1][1].append(trechos[-2][1][-1])
        trechos[-1][1].append((passo["coluna"], passo["linha"]))

    itens = []
    for i, (chaves, pontos) in enumerate(trechos):
        cor = CORES_CAMADA[i % len(CORES_CAMADA)]
        # cada trecho e deslocado um pouco, para quando o caminho volta pelo mesmo corredor
        desloc = (i - (len(trechos) - 1) / 2) * 0.13
        xs = [p[0] + desloc for p in pontos]
        ys = [p[1] + desloc for p in pontos]
        ax.plot(xs, ys, color=cor, linewidth=3, alpha=0.85, solid_capstyle="round")
        texto = "sem chave" if chaves == "-" else "com chaves " + ",".join(chaves)
        itens.append(plt.Line2D([0], [0], color=cor, linewidth=3, label=texto))

    inicio = percurso[0]
    fim = percurso[-1]
    ax.plot(inicio["coluna"], inicio["linha"], "o", color="black", markersize=9)
    ax.plot(fim["coluna"], fim["linha"], "*", color="black", markersize=14)
    itens.append(plt.Line2D([0], [0], marker="o", color="black", linestyle="", label="início"))
    itens.append(plt.Line2D([0], [0], marker="*", color="black", linestyle="", markersize=12, label="saída"))

    ax.add_artist(legenda_mapa)
    ax.legend(handles=itens, title="percurso", loc="upper left", bbox_to_anchor=(1.01, 1), frameon=False)
    return fig, ax


def desenhar_heatmap(linhas, multiplicidade, titulo):
    """Pinta cada casa pela multiplicidade (quantos estados de G_est ficam nela).

    multiplicidade: dicionario (linha, coluna) -> numero de estados.
    """
    from matplotlib.colors import BoundaryNorm

    altura = len(linhas)
    largura = len(linhas[0])
    maximo = max(multiplicidade.values())
    valores = []
    tem_nao_alcancada = False
    for lin in range(altura):
        linha_valores = []
        for col in range(largura):
            if linhas[lin][col] == "#":
                linha_valores.append(-1)                      # parede
            elif (lin, col) not in multiplicidade:
                linha_valores.append(0)                       # casa livre nunca alcancada
                tem_nao_alcancada = True
            else:
                linha_valores.append(multiplicidade[(lin, col)])
        valores.append(linha_valores)

    # uma cor para cada valor inteiro: parede, 0, 1, 2, ..., maximo
    cores = ["#3a3a3a", "#e0e0e0"] + [plt.get_cmap("viridis")(i / max(1, maximo - 1)) for i in range(maximo)]
    from matplotlib.colors import ListedColormap
    cmap = ListedColormap(cores)
    norm = BoundaryNorm([x - 0.5 for x in range(-1, maximo + 2)], cmap.N)

    lado = min(0.55, 16 / largura)
    fig, ax = plt.subplots(figsize=(largura * lado + 2.0, altura * lado + 1.6))
    imagem = ax.imshow(valores, cmap=cmap, norm=norm, interpolation="nearest")
    barra = fig.colorbar(imagem, ax=ax, fraction=0.025, pad=0.02, ticks=list(range(1, maximo + 1)))
    barra.ax.set_ylim(0.5, maximo + 0.5)
    barra.set_label("número de estados na casa (multiplicidade)")

    ax.set_xlabel("coluna")
    ax.set_ylabel("linha")
    ax.set_title(titulo)
    itens = [Patch(facecolor="#3a3a3a", label="parede")]
    if tem_nao_alcancada:
        itens.append(Patch(facecolor="#e0e0e0", edgecolor="#9e9e9e", label="casa livre não alcançada"))
    ax.legend(handles=itens, loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=2, frameon=False)
    return fig, ax


def _desenhar_arcos(ax, posicoes, arcos, cor, largura, estilo="-|>"):
    from matplotlib.patches import FancyArrowPatch
    for u, v in arcos:
        seta = FancyArrowPatch(posicoes[u], posicoes[v], arrowstyle=estilo, mutation_scale=8,
                               color=cor, linewidth=largura, shrinkA=6, shrinkB=6,
                               connectionstyle="arc3,rad=0.12")
        ax.add_patch(seta)


def desenhar_camadas(g_est, titulo):
    """Desenha o G_est com uma faixa por conjunto de chaves (camada).

    g_est: grafo de estados SEM o ALVO. Dentro da faixa, cada estado fica na
    posicao da sua casa no mapa (coluna no eixo x, linha no eixo y).
    """
    from src.graphs.estados import decompor_estado

    camadas = []
    camada_de = {}
    for no in g_est.nos():
        posicao, chaves, bonus = decompor_estado(no)
        if chaves not in camadas:
            camadas.append(chaves)
        camada_de[no] = chaves

    altura_mapa = max(decompor_estado(no)[0][0] for no in g_est.nos()) + 1
    espaco = altura_mapa + 2
    posicoes = {}
    for no in g_est.nos():
        (lin, col), chaves, bonus = decompor_estado(no)
        indice = camadas.index(chaves)
        posicoes[no] = (col, -(lin + indice * espaco))

    dentro = []
    entre = []
    for u in g_est.nos():
        for v, peso, mov, casa in g_est.vizinhos(u):
            if camada_de[u] == camada_de[v]:
                dentro.append((u, v))
            else:
                entre.append((u, v))

    fig, ax = plt.subplots(figsize=(11, 2.2 * len(camadas) + 1.5))
    _desenhar_arcos(ax, posicoes, dentro, "#9e9e9e", 0.8)
    _desenhar_arcos(ax, posicoes, entre, "#d62728", 2.2)

    for i, chaves in enumerate(camadas):
        nos = [no for no in g_est.nos() if camada_de[no] == chaves]
        cor = CORES_CAMADA[i % len(CORES_CAMADA)]
        ax.scatter([posicoes[n][0] for n in nos], [posicoes[n][1] for n in nos],
                   s=60, color=cor, zorder=3, edgecolor="black", linewidth=0.5)
        nome = "camada sem chave (-)" if chaves == "-" else f"camada com chaves {chaves}"
        ax.text(-1.2, -(i * espaco) - altura_mapa / 2 + 0.5, nome, ha="right", va="center", fontsize=10, color=cor)

    for u, v in entre:
        (lin, col), chaves, bonus = decompor_estado(v)
        ax.annotate(f"pega a chave em ({lin},{col})", posicoes[v], xytext=(8, -14),
                    textcoords="offset points", fontsize=9, color="#d62728")

    ax.set_title(titulo)
    ax.set_xlabel("coluna da casa no mapa")
    ax.set_ylabel("linha da casa (uma faixa por camada)")
    ax.set_yticks([])
    maior_coluna = max(p[0] for p in posicoes.values())
    ax.set_xlim(-8, maior_coluna + 2)
    ax.set_xticks(range(0, maior_coluna + 1))
    ax.legend(handles=[
        plt.Line2D([0], [0], marker="o", color="white", markerfacecolor=CORES_CAMADA[0], markeredgecolor="black", markersize=8, label="estado"),
        plt.Line2D([0], [0], color="#9e9e9e", linewidth=1, label="arco dentro da camada"),
        plt.Line2D([0], [0], color="#d62728", linewidth=2.2, label="arco que muda de camada"),
    ], loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=3, frameon=False)
    for borda in ax.spines.values():
        borda.set_visible(False)
    return fig, ax


def desenhar_arvore_bfs(g_est, inicio, titulo):
    """Desenha a arvore da BFS: cada coluna e um nivel (distancia ao inicio)."""
    from src.graphs.algorithms import bfs
    from src.graphs.estados import NO_ALVO, decompor_estado

    dist, pai, ordem = bfs(g_est, inicio)
    niveis = {}
    for no in ordem:
        niveis.setdefault(dist[no], []).append(no)

    posicoes = {}
    for nivel, nos in niveis.items():
        for i, no in enumerate(nos):
            posicoes[no] = (nivel, -(i - (len(nos) - 1) / 2))

    camadas = []
    for no in ordem:
        if no != NO_ALVO:
            chaves = decompor_estado(no)[1]
            if chaves not in camadas:
                camadas.append(chaves)

    fig, ax = plt.subplots(figsize=(max(10, len(niveis) * 0.42), 4.5))
    for no in ordem:
        if pai[no] is not None:
            (x1, y1), (x2, y2) = posicoes[pai[no]], posicoes[no]
            ax.plot([x1, x2], [y1, y2], color="#9e9e9e", linewidth=1, zorder=1)

    for i, chaves in enumerate(camadas):
        nos = [n for n in ordem if n != NO_ALVO and decompor_estado(n)[1] == chaves]
        texto = "estado sem chave" if chaves == "-" else f"estado com chaves {chaves}"
        ax.scatter([posicoes[n][0] for n in nos], [posicoes[n][1] for n in nos], s=45,
                   color=CORES_CAMADA[i % len(CORES_CAMADA)], edgecolor="black", linewidth=0.5,
                   zorder=2, label=texto)
    if NO_ALVO in posicoes:
        ax.scatter(*posicoes[NO_ALVO], s=120, marker="*", color="black", zorder=3, label="ALVO")
    ax.annotate("início", posicoes[inicio], xytext=(0, 10), textcoords="offset points", ha="center", fontsize=9)

    ax.set_title(titulo)
    ax.set_xlabel("nível da BFS (número de passos desde o início)")
    ax.set_xticks(range(0, len(niveis), 5 if len(niveis) > 20 else 1))
    ax.set_yticks([])
    ax.set_ylabel("estados do mesmo nível")
    ax.grid(axis="x", color="#eeeeee")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.18), ncol=4, frameon=False)
    for borda in ("top", "right", "left"):
        ax.spines[borda].set_visible(False)
    return fig, ax