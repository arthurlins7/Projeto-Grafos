# Projeto Grafos

Projeto acadêmico desenvolvido em **Python** para as disciplinas de **Teoria dos Grafos** e **Análise e Visualização de Dados (AVD)**, no semestre **2026.2**. O objetivo é aplicar grafos dirigidos para representar problemas, explorar conexões e comparar diferentes formas de encontrar caminhos, utilizando os algoritmos **BFS, DFS, Dijkstra e Bellman-Ford**.

O trabalho combina modelagem de grafos, análise de desempenho e visualização de dados em dois cenários: labirintos com regras de movimentação e relações entre usuários do dataset **Slashdot**. A proposta é compreender como a estrutura do grafo e os pesos das ligações influenciam os percursos, os resultados e o tempo de execução dos algoritmos.

- **Parte 1:** representar labirintos com chaves, portas e bônus como grafos de estados e comparar os percursos dos algoritmos.
- **Parte 2:** estudar a rede de usuários do Slashdot, comparando os algoritmos, o desempenho e os resultados da exploração dos dados.

## Estrutura do projeto

```text
src/        Leitura, estrutura do grafo, algoritmos, execução e visualização
data/       Mapas e dataset do Slashdot
notebooks/  01: exploração dos dados (AVD) · 02: algoritmos da Parte 2 (Grafos)
tests/      Testes automatizados
docs/       Documentação e materiais da entrega
out/        Resultados e figuras
```

## Estado atual

- Grafo dirigido e algoritmos BFS, DFS, Dijkstra e Bellman-Ford implementados no próprio projeto (sem bibliotecas prontas) e testados com `pytest`.
- Parte 1: leitura e validação dos mapas, grafo de posições e grafo de estados; `src.solve` gera as saídas e as figuras em `out/parte1/`.
- Parte 2: exploração dos dados no notebook `01_exploracao_dados.ipynb`, algoritmos e medições no notebook `02_grafos_algoritmos.ipynb` e execução pelo terminal com `--dataset`.
- Parte 2: visualizações de comparação dos algoritmos e de análise dos dados em `out/parte2/`.
- Parte 1: mapas do grupo em `data/mapas_grupo/`, comandos pelo terminal (`--alg`, `--armadilhas`, `--fonte-consumivel`, `--interactive` e `--out`) e página interativa em `out/parte1/labirinto_interativo.html`.
- Site do grupo em `web/`: o mesmo conteúdo da página interativa, em várias páginas.
- Relatório em PDF e declaração de uso de IA em `docs/`.

## Instalação

Requer **Git** e **Python 3.11 ou superior**. No PowerShell:

```powershell
git clone https://github.com/arthurlins7/Projeto-Grafos.git
cd Projeto-Grafos
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Se já tiver o projeto clonado, comece pela criação da `.venv` na raiz do projeto.

## Uso

Execute os comandos a partir da raiz do projeto.

### Validar um mapa

```powershell
.\.venv\Scripts\python.exe -m src.cli --mapa data/mapas/m01_terreno.txt --validar-mapa
```

Saída esperada:

```text
Mapa valido: 5 linhas e 13 colunas.
```

O comando verifica o formato e mostra as dimensões. Um mapa válido não necessariamente possui solução. Para consultar a ajuda, use `.\.venv\Scripts\python.exe -m src.cli --help`.

### Gerar as saídas da Parte 1

```powershell
.\.venv\Scripts\python.exe -m src.solve
```

Gera em `out/parte1/` os arcos, as métricas, as camadas, os graus, as soluções dos algoritmos e as figuras de todos os mapas de `data/mapas/` e `data/mapas_grupo/`, além da página interativa e do `web/data.js`.

### Rodar um algoritmo num mapa (Parte 1)

```powershell
.\.venv\Scripts\python.exe -m src.cli --mapa ./data/mapas/m03_tres_chaves.txt --alg BFS --out ./out/parte1/
.\.venv\Scripts\python.exe -m src.cli --mapa ./data/mapas/m03_tres_chaves.txt --alg DIJKSTRA --out ./out/parte1/
.\.venv\Scripts\python.exe -m src.cli --mapa ./data/mapas/m05_bonus.txt --alg BELLMAN_FORD --out ./out/parte1/
.\.venv\Scripts\python.exe -m src.cli --mapa ./data/mapas/m06_fonte.txt --alg BELLMAN_FORD --fonte-consumivel --out ./out/parte1/
.\.venv\Scripts\python.exe -m src.cli --mapa ./data/mapas/m04_esteiras.txt --armadilhas --out ./out/parte1/
```

| Opção | Significado |
| --- | --- |
| `--alg` | `BFS`, `DFS`, `DIJKSTRA` ou `BELLMAN_FORD`, rodado no grafo de estados do mapa |
| `--fonte-consumivel` | A fonte (`*`) vale −2 só na primeira vez, como o bônus (correção do ciclo negativo do m06) |
| `--armadilhas` | Lista os estados alcançáveis de onde não dá mais para chegar na saída |
| `--out` | Pasta onde o resultado é salvo: `<mapa>_<algoritmo>.json` para o `--alg` e `armadilhas_<mapa>.csv` para o `--armadilhas` |

O comando funciona com qualquer mapa válido, não só os de `data/mapas/`. Quando o Bellman-Ford encontra um ciclo negativo de onde ainda dá para chegar na saída, mostra o ciclo e o custo dele; se o ciclo fica num lugar de onde não se chega mais na saída, o custo até a saída continua sendo calculado, com um aviso.

### Página interativa (Parte 1)

```powershell
.\.venv\Scripts\python.exe -m src.cli --interactive
.\.venv\Scripts\python.exe -m src.cli --mapa ./data/mapas/m03_tres_chaves.txt --interactive --out ./out/parte1/
```

Abre `out/parte1/labirinto_interativo.html` no navegador. É o site do grupo (pasta `web/`) num arquivo só, com os dados e as figuras dentro, então funciona sem servidor. Com `--mapa`, a página é gerada de novo com esse mapa incluído (inclusive um mapa novo, fora de `data/mapas/`) e já abre nele. Com `--out`, a página é salva nessa pasta.

Na página **Labirintos e saídas** dá para escolher o mapa e o algoritmo, acompanhar o percurso passo a passo (com controle de velocidade), comparar os quatro algoritmos lado a lado, alternar as camadas, realçar os estados-armadilha, explorar os arcos, graus e caminhos de cada mapa, ver o grafo de estados em camadas, a árvore da BFS e o heatmap de multiplicidade, e abrir todos os arquivos de `out/parte1/`.

O site em `web/` pode ser aberto direto pelo `web/index.html`. Os dados dele ficam em `web/data.js`, gerado pelo `src.solve` (ou por `python web/build_data.py`).

### Rodar um algoritmo no dataset (Parte 2)

```powershell
.\.venv\Scripts\python.exe -m src.cli --dataset data/dataset_parte2/ --alg DIJKSTRA --source 9765 --target 3451 --out out/parte2/
```

| Opção | Significado |
| --- | --- |
| `--alg` | `BFS`, `DFS`, `DIJKSTRA` ou `BELLMAN_FORD` |
| `--source` | Usuário de partida |
| `--target` | Usuário de chegada (opcional) |
| `--recorte` | `10`, `50` ou `100`: porcentagem dos usuários, com os mesmos recortes do notebook (padrão: `100`) |
| `--out` | Pasta onde o resultado é salvo em JSON (padrão: `out/parte2/`) |

BFS e DFS contam passos. O Dijkstra usa amigo = 1 e inimigo = 2, porque não aceita peso negativo. O Bellman-Ford usa os sinais originais (+1 e −1) e, quando encontra um ciclo negativo, mostra o ciclo e o custo dele. Exemplos sem ciclo negativo (recorte de 10%) e com ciclo negativo (rede completa):

```powershell
.\.venv\Scripts\python.exe -m src.cli --dataset data/dataset_parte2/ --alg BELLMAN_FORD --source 11038 --recorte 10
.\.venv\Scripts\python.exe -m src.cli --dataset data/dataset_parte2/ --alg BELLMAN_FORD --source 11038
```

### Medir o desempenho (Parte 2)

```powershell
.\.venv\Scripts\python.exe -m src.cli --dataset data/dataset_parte2/ --benchmark --out out/parte2/
```

Mede os quatro algoritmos nos recortes de 10%, 50% e 100% (5 execuções cada), o Dijkstra nas dez marcações do piloto e os dois casos do Bellman-Ford. O resultado é gravado em `out/parte2/parte2_report.json`, no mesmo formato gerado pelo notebook `02_grafos_algoritmos.ipynb`.

## Dataset da Parte 2

Utilizamos o **Slashdot Zoo**, versão `soc-sign-Slashdot090221`, aprovada para o projeto. A base contém **82.140 usuários e 549.202 relações dirigidas**, com sinais `1` (amigo) e `-1` (inimigo).

O arquivo está em `data/dataset_parte2/soc-sign-Slashdot090221.txt.gz` e pode ser lido sem descompactar. Em Python, a partir da raiz do projeto:

```python
from src.graphs.io import ler_dataset, montar_grafo_dataset

dados = ler_dataset("data/dataset_parte2/soc-sign-Slashdot090221.txt.gz")
grafo = montar_grafo_dataset(dados)
print(grafo.ordem(), grafo.tamanho())  # 82140 549202
```

A tabela possui as colunas `origem`, `destino` e `sinal`. O objeto `grafo` é criado na memória e preserva a direção e os pesos dos registros.

- [Fonte e download — SNAP / Stanford](https://snap.stanford.edu/data/soc-sign-Slashdot090221.html).
- Referência: J. Leskovec, D. Huttenlocher e J. Kleinberg. *Signed Networks in Social Media*. CHI 2010.
- [01_exploracao_dados.ipynb](notebooks/01_exploracao_dados.ipynb): exploração dos dados (AVD), com estrutura, distribuições, relações e outliers.
- [02_grafos_algoritmos.ipynb](notebooks/02_grafos_algoritmos.ipynb): amostragem, BFS, DFS, Dijkstra, Bellman-Ford, escalabilidade e relatório de desempenho. Gera `out/parte2/parte2_report.json` e `out/parte2/passos_volta.csv`.

Abra os notebooks, selecione o Python da `.venv` e execute as células em ordem.

O notebook `02` gera `out/parte2/passos_volta.csv`, que o notebook `01` usa. Quando for preciso regenerar esse arquivo, rode o `02` e depois o `01`. Ao reexecutar as medições (notebook `02` ou `--benchmark`), os tempos variam conforme a máquina e a carga do sistema. Os valores citados no projeto correspondem à rodada de referência.

## Testes

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Os testes verificam a estrutura do grafo, os algoritmos, a leitura dos mapas e os comandos do terminal das duas partes. `networkx` é utilizado somente nos testes para conferir resultados; os algoritmos são implementados no próprio projeto, sem bibliotecas prontas.

## Equipe e contato

Arthur Lins, Davi Santiago, João Pedro Patriota e Lucas Ramon.
