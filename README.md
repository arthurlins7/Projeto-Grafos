# Projeto Grafos

Projeto acadêmico desenvolvido em **Python** para as disciplinas de **Teoria dos Grafos** e **Análise e Visualização de Dados (AVD)**, no semestre **2026.2**. O objetivo é aplicar grafos dirigidos para representar problemas, explorar conexões e comparar diferentes formas de encontrar caminhos, utilizando os algoritmos **BFS, DFS, Dijkstra e Bellman-Ford**.

O trabalho combina modelagem de grafos, análise de desempenho e visualização de dados em dois cenários: labirintos com regras de movimentação e relações entre usuários do dataset **Slashdot**. A proposta é compreender como a estrutura do grafo e os pesos das ligações influenciam os percursos, os resultados e o tempo de execução dos algoritmos.

- **Parte 1:** representar labirintos com chaves, portas e bônus como grafos de estados e comparar os percursos dos algoritmos.
- **Parte 2:** estudar a rede de usuários do Slashdot, comparando os algoritmos, o desempenho e os resultados da exploração dos dados.

## Estrutura do projeto

```text
src/        Leitura, estrutura do grafo, algoritmos, execução e visualização
data/       Mapas e dataset do Slashdot
notebooks/  Exploração e visualização dos dados
tests/      Testes automatizados
docs/       Documentação e materiais da entrega
out/        Resultados e figuras
```

## Estado atual

- Estrutura de grafo dirigido e algoritmos BFS, DFS, Dijkstra e Bellman-Ford implementados.
- Leitura e validação dos mapas disponíveis pelo terminal.
- Leitura, validação e construção do grafo do dataset implementadas.
- Base de desenho dos mapas e início do notebook de exploração preparados.

A construção dos grafos dos labirintos, a integração das buscas pelo terminal e os experimentos da Parte 2 ainda estão em desenvolvimento.

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
- [Notebook de exploração inicial](notebooks/01_exploracao_dados.ipynb): descrição das colunas, leitura e primeiras linhas. Abra o notebook, selecione o Python da `.venv` e execute as células em ordem.

## Testes

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Os testes verificam a estrutura do grafo, os algoritmos, a leitura dos mapas e o comando do terminal. `networkx` é utilizado somente nos testes para conferir resultados; os algoritmos são implementados pelo grupo.

## Equipe e contato

Arthur Lins, Davi Santiago, João Pedro Patriota e Lucas Ramon.
