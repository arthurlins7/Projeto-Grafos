# Visualizacoes da Parte 1 (figuras da Secao 8).
# [IA] Claude – codigo de desenho com matplotlib (uso permitido: apoio com
# bibliotecas de visualizacao). Cores, titulo e legenda foram escolhidos pelo grupo.

import matplotlib.pyplot as plt
from matplotlib.colors import to_rgb
from matplotlib.patches import Patch


# ----------------------------------------------------------------------------
# CONFIGURACAO VISUAL (escolhas do grupo) - para mudar o visual, mude so aqui.
# ----------------------------------------------------------------------------

# Os 8 primeiros sao as cores da Figura 1 do enunciado.
# Esteira, bonus e fonte foram escolhidos pelo grupo.
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
