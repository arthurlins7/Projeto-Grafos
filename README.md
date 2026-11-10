# Projeto Final

Projeto interdisciplinar de **Teoria dos Grafos** e **Análise e Visualização de Dados (AVD)** — 2026.2.

> **Status:** em desenvolvimento — estrutura do grafo, quatro algoritmos e leitura/validação de mapas implementados. Também foi feita a base de desenho do mapa (`viz.py`). A integração das buscas com os mapas ainda está pendente. Na Parte 2, o dataset Slashdot já é lido, validado e convertido em grafo dirigido.
---

## Sobre o projeto

O projeto tem duas partes:

1. **Parte 1 — Labirinto com Chaves e Portas.** Modelar labirintos em grade como um **grafo de estados**, em que cada nó é `(linha, coluna, chaves, bônus consumidos)`, e não apenas uma casa do mapa. Sobre esse grafo rodamos BFS, DFS, Dijkstra e Bellman-Ford, comparamos com o modelo ingênuo (grafo de posições) e visualizamos os percursos.
2. **Parte 2 — Dataset maior.** Escolher um dataset real de grafo **dirigido e ponderado**, com **pesos negativos vindos dos próprios dados**, e comparar os quatro algoritmos em **corretude e desempenho**, com análise exploratória e explanatória dos dados (AVD).

Todos os algoritmos de grafos (BFS, DFS, Dijkstra, Bellman-Ford) e a construção do grafo de estados são **implementação própria** do grupo.

---

## Parte 1 — Labirinto com Chaves (Grafo de Estados)

### Ideia central

O mapa **não é o grafo**. Uma mesma casa do labirinto corresponde a vários nós — um para cada combinação de chaves que o jogador tem e de bônus que já consumiu ao chegar nela.

### Símbolos dos mapas

| Símbolo                 | Significado                                              | Custo de entrar          |
| ----------------------- | -------------------------------------------------------- | ------------------------ |
| `#`                     | Parede (intransponível)                                  | —                        |
| `.`                     | Chão                                                     | 1                        |
| `S`                     | Início (exatamente um por mapa)                          | 1                        |
| `G`                     | Saída (pelo menos uma); ao entrar, o jogo termina        | 1                        |
| `,`                     | Lama                                                     | 3                        |
| `~`                     | Água                                                     | 5                        |
| `a`–`d`                 | Chave (o jogador fica com ela para sempre)               | 1                        |
| `A`–`D`                 | Porta (só passa quem tem a chave correspondente)         | 1                        |
| `>` `<` `^` `v`         | Esteira (estando nela, só se move na direção da seta)    | 1                        |
| `+`                     | Bônus consumível                                         | −4 na 1ª vez, depois 1   |
| `*`                     | Fonte de energia (não se esgota)                         | −2 sempre                |

Linhas iniciadas com `;` são comentários.

### Regras de movimento

- Quatro direções, sempre testadas na ordem **N, L, S, O**.
- Custo do movimento = custo da casa de destino.
- Não é possível sair da grade nem entrar em parede.
- Estados posicionados em `G` não têm arcos de saída.

### Modelagem

- **`G_pos`** — grafo de posições: um nó por casa livre (modelo ingênuo, usado para comparação).
- **`G_est`** — grafo de estados: um nó por estado `(linha, coluna, chaves, bônus)`, construído **por exploração** a partir do estado inicial (só estados alcançáveis).
- Rótulo dos estados: `(3,5)|ab|{0,2}` — sem chaves, `-`; sem bônus, `{}`.
- Nó virtual **`ALVO`**, com arco de custo 0 saindo de todo estado em `G`.
- Grafo **dirigido**, sem espelhamento de arcos.

### Mapas fornecidos (`data/mapas/`)

| Arquivo                 | O que exercita                                                      |
| ----------------------- | ------------------------------------------------------------------- |
| `m01_terreno.txt`       | Custos de terreno: o caminho com menos passos não é o mais barato   |
| `m02_uma_chave.txt`     | Uma chave e uma porta                                               |
| `m03_tres_chaves.txt`   | Três chaves com ordem de coleta obrigatória                         |
| `m04_esteiras.txt`      | Arcos de mão única, becos e estados-armadilha                       |
| `m05_bonus.txt`         | Bônus consumíveis: pesos negativos sem ciclo negativo               |
| `m06_fonte.txt`         | Fonte de energia: ciclo negativo (um "exploit" do jogo)             |
| `m07_impossivel.txt`    | Mapa sem solução                                                    |
| `m08_grande.txt`        | Mapa 31×71 com 4 chaves                                             |

Além deles, o grupo criará **dois mapas próprios** em `data/mapas_grupo/`.

### Entregas da Parte 1

- [X] Leitura e validação dos mapas
- [ ] Construção de `G_pos` e `G_est` (com teto teórico × estados alcançáveis)
- [ ] Exportação das arestas por mapa
- [ ] Métricas globais e por camada (ordem, tamanho, densidade), arcos entre camadas
- [ ] Graus, rankings, multiplicidade das casas e becos
- [ ] Comparação de modelagens (portas como chão × como parede × `G_est`) em m02, m03 e m04
- [ ] Bellman-Ford no m05 (`G_pos` × `G_est`) e prova da ausência de ciclo negativo no `G_est`
- [ ] BFS, Dijkstra, Bellman-Ford e DFS (com classificação de arcos) em todos os mapas
- [ ] Estados-armadilha (m04 e m07)
- [ ] Correção de regra do m06 (`--fonte-consumivel`)
- [ ] Visualizações: percursos (m03, m08), grafo em camadas e árvore BFS (m02), heatmap de multiplicidade (m08)
  - [x] Base de desenho do mapa (`viz.py`)
- [ ] Apresentação interativa (HTML ou Streamlit)
- [ ] Dois mapas do grupo com gabarito

---

## Parte 2 — Dataset Maior, Comparação de Algoritmos e Análise Visual

> **Dataset (aprovado):** Slashdot Zoo signed social network, fevereiro de 2009 — [SNAP / Stanford](https://snap.stanford.edu/data/soc-sign-Slashdot090221.html).

| Atributo | Valor (fonte: SNAP) |
| --- | --- |
| Arquivo | `soc-sign-Slashdot090221.txt.gz` |
| Nós | 82.140 |
| Arestas | 549.202 |
| Tipo | dirigido, ponderado (sinal da relação) |
| Colunas | `FromNodeId`, `ToNodeId`, `Sign` (+1 amigo, −1 inimigo) |

**Como obter:** baixe `soc-sign-Slashdot090221.txt.gz` na página acima e salve em `data/dataset_parte2/` (não é preciso descompactar).

**Citação:** J. Leskovec, D. Huttenlocher, J. Kleinberg. *Signed Networks in Social Media*. CHI 2010.

### Requisitos do dataset

- Grafo **dirigido e ponderado** (se a fonte for não dirigida, justificar a direção).
- Pelo menos **20.000 arestas** (acima de ~500 mil, justificar a amostragem).
- **Pesos negativos vindos dos dados**, com significado no domínio.
- Não são permitidos datasets de malha aérea nem labirintos/grades gerados.
- Uma **pergunta de pesquisa** sobre o domínio que os algoritmos ajudem a responder.

### Entregas da Parte 2

- [x] Leitura, validação e montagem do grafo do dataset (`io.py`)
- [ ] Descrição e exploração do dataset (visão de grafos e visão de dados/AVD)
- [ ] BFS/DFS a partir de ≥ 3 fontes distintas
- [ ] Dijkstra com pesos ≥ 0 em ≥ 5 pares origem–destino (com a transformação de pesos documentada)
- [ ] Bellman-Ford: um caso com peso negativo sem ciclo negativo e um caso com ciclo negativo
- [ ] Métricas de desempenho (média de ≥ 5 execuções)
- [ ] Escalabilidade em ≥ 3 tamanhos do grafo, comparada com a complexidade teórica
- [ ] Discussão crítica e resposta à pergunta de pesquisa
- [ ] ≥ 6 visualizações (4 exploratórias + 2 explanatórias), cada uma com nota analítica

---

## Estrutura do repositório

```
projeto-grafos/
├── README.md
├── requirements.txt
├── docs/
│   └── DECLARACAO_IA.pdf      # declaração de uso de IA assinada por todos
├── data/
│   ├── mapas/                 # mapas fornecidos (m01 a m08)
│   ├── mapas_grupo/           # 2 mapas criados pelo grupo
│   └── dataset_parte2/        # dataset maior (Parte 2)
├── out/
│   ├── parte1/
│   └── parte2/
├── src/
│   ├── cli.py
│   ├── solve.py
│   ├── graphs/
│   │   ├── io.py              # ler/validar os mapas e o dataset
│   │   ├── estados.py         # grafo de posições e grafo de estados
│   │   ├── graph.py           # lista de adjacência DIRIGIDA
│   │   └── algorithms.py      # BFS, DFS, Dijkstra, Bellman-Ford (próprios)
│   └── viz.py                 # visualizações/UX
└── tests/
    ├── test_graph.py
    ├── test_cli.py
    ├── test_bfs.py
    ├── test_dfs.py
    ├── test_dijkstra.py
    ├── test_bellman_ford.py
    ├── test_estados.py
    └── test_io.py
```

---

## Requisitos e restrições técnicas

- **Python 3.11+**.
- Bibliotecas permitidas: `pandas` (IO), `argparse`, `heapq`, `dataclasses`, `typing`; `matplotlib`, `plotly`, `pyvis` e `streamlit` apenas para visualização/UX.
- **Proibido** usar bibliotecas que já implementem BFS, DFS, Dijkstra ou Bellman-Ford (ex.: `networkx`, `igraph`, `graph-tool`).
- Exceção: `networkx` pode ser usado **somente em `tests/`**, como oráculo para conferir resultados.

---

## Como executar

### Instalação e testes (PowerShell)

Execute na raiz do repositório:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pytest -q
```

### Validar um mapa

```powershell
.\.venv\Scripts\python.exe -m src.cli --mapa data/mapas/m01_terreno.txt --validar-mapa
```

Saída esperada:

```text
Mapa valido: 5 linhas e 13 colunas.
```

O comando verifica linhas, largura, símbolos, exatamente um início `S` e pelo menos uma saída `G`. Aceita UTF-8 com ou sem BOM e quebras de linha do Windows. Linhas iniciadas com `;` são ignoradas; espaços e linhas vazias dentro do mapa são considerados erros.

A validação confere o formato do arquivo. Um mapa válido pode não ter solução, como o `m07`; as buscas ainda não estão integradas ao comando.

O código de saída é `0` para mapa válido e `2` para erros de leitura, codificação, formato ou argumentos. A mensagem de símbolo inválido indica linha e coluna do mapa, contando a partir de 1 e sem contar comentários. Para consultar a ajuda:

```powershell
.\.venv\Scripts\python.exe -m src.cli --help
```

### Localizar início e saídas em Python

Depois de ler o mapa, use `localizar_inicio_e_saidas` para obter a posição do início e a lista de saídas:

```python
from src.graphs.io import ler_mapa, localizar_inicio_e_saidas

linhas = ler_mapa("data/mapas/m01_terreno.txt")
inicio, saidas = localizar_inicio_e_saidas(linhas)
```

As coordenadas seguem o formato `(linha, coluna)`, contando a partir de zero e sem contar comentários. Para o `m01`, o início é `(1, 1)` e as saídas são `[(1, 11)]`. A lista de saídas segue a ordem de leitura do mapa: linha e depois coluna. A função também valida o mapa antes de localizar as posições.

### Ler o dataset da Parte 2 em Python

Use `ler_dataset` para ler e validar o arquivo e `montar_grafo_dataset` para criar o grafo dirigido:

```python
from src.graphs.io import ler_dataset, montar_grafo_dataset

dados = ler_dataset("data/dataset_parte2/soc-sign-Slashdot090221.txt.gz")
grafo = montar_grafo_dataset(dados)
print(grafo.ordem(), grafo.tamanho())   # 82140 549202
```

`ler_dataset` devolve uma tabela com as colunas `origem`, `destino` e `sinal`, todas inteiras. O arquivo `.gz` é lido sem descompactar, e as linhas iniciadas com `#` são ignoradas. A leitura gera `ValueError` com mensagem clara para arquivo vazio, número de colunas diferente de três, valores vazios, valores não inteiros, sinal diferente de `1` ou `-1` e codificação diferente de UTF-8.

Em `montar_grafo_dataset`, cada linha vira um arco `origem → destino` com peso igual ao sinal (`+1` amigo, `-1` inimigo). A montagem do grafo completo leva alguns segundos.

### Execução das buscas (planejada)

> Os comandos abaixo descrevem funcionalidades futuras. Ainda não estão disponíveis em `src/cli.py` e `src/solve.py`.

```bash
# Parte 1 (labirintos)
python -m src.cli --mapa ./data/mapas/m03_tres_chaves.txt --alg BFS --out ./out/parte1/
python -m src.cli --mapa ./data/mapas/m03_tres_chaves.txt --alg DIJKSTRA --out ./out/parte1/
python -m src.cli --mapa ./data/mapas/m05_bonus.txt --alg BELLMAN_FORD --out ./out/parte1/
python -m src.cli --mapa ./data/mapas/m06_fonte.txt --alg BELLMAN_FORD --fonte-consumivel --out ./out/parte1/
python -m src.cli --mapa ./data/mapas/m04_esteiras.txt --armadilhas --out ./out/parte1/
python -m src.cli --mapa ./data/mapas/m03_tres_chaves.txt --interactive --out ./out/parte1/

# Parte 2 (dataset maior)
python -m src.cli --dataset ./data/dataset_parte2/ --alg DIJKSTRA --source A --target Z --out ./out/parte2/
python -m src.cli --dataset ./data/dataset_parte2/ --benchmark --out ./out/parte2/
```

---

## Saídas previstas

**Parte 1 (`out/parte1/`)**

- `arestas_<mapa>.csv`, `graus_<mapa>.csv`
- `metricas_global.json`, `camadas.json`
- `comparacao_modelagem.csv`, `solucoes.csv`, `dfs_classificacao.csv`
- `percurso_m03.json`, `ciclo_negativo_m06.json`
- `armadilhas_m04.csv`, `armadilhas_m07.csv`
- `percurso_m03.png`, `percurso_m08.png` e demais figuras
- `labirinto_interativo.html` (ou app Streamlit)

**Parte 2 (`out/parte2/`)**

- `parte2_report.json`
- Visualizações da Parte 2 (imagens/HTML)

---

## Testes

Testes com `pytest`:

- **Grafo:** nós, arcos dirigidos, graus, métricas, transposto, subgrafo e preservação do original.
- **CLI:** execução em subprocesso com os oito mapas, ajuda, argumentos incorretos e erros de arquivo, codificação e formato.
- **BFS:** níveis corretos em grafo pequeno.
- **DFS:** detecção de ciclo e classificação de arcos em grafo dirigido.
- **Dijkstra:** caminhos corretos com pesos ≥ 0; recusa de grafo com peso negativo.
- **Bellman-Ford:** distâncias corretas com pesos negativos sem ciclo; detecção e retorno do ciclo negativo.
- **Estados (planejado):** mapa mínimo do grupo (até 5×7) com número de estados e arcos conferido à mão; esteira para parede gera estado sem saída; coletar chave muda de camada.
- **IO:** mapas válidos e inválidos, comentários, BOM, quebras de linha, espaços indevidos, localização do início e das saídas e dimensões dos oito mapas fornecidos.

---

## Cronograma

| Etapa                                       | Data                        |
| ------------------------------------------- | --------------------------- |
| Proposta do dataset da Parte 2 (checkpoint) | até 12/10/2026              |
| Acompanhamentos em sala (Grafos)            | 10/11, 17/11, 19/11 e 24/11 |
| Acompanhamentos em sala (AVD)               | 17/11, 19/11 e 24/11        |
| Entrega do material                         | 26/11/2026                  |
| Apresentações                               | 26/11, 01/12 e 03/12        |

---

## Uso de IA generativa

O uso de IA segue as regras do enunciado e é registrado em [`docs/DECLARACAO_IA.pdf`](docs/DECLARACAO_IA.pdf). Trechos de código feitos com apoio de IA são marcados com:

```python
# [IA] <ferramenta> - <finalidade>
```

---

## Equipe

| Integrante           | Pacotes de trabalho |
| -------------------- | ------------------- |
| Arthur Lins          | a definir           |
| Davi Santiago        | a definir           |
| João Pedro Patriota  | a definir           |
| Lucas Ramon          | a definir           |
