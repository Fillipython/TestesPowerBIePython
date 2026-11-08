# TestesPowerBIePython

Projeto de processamento, analise estatistica e visualizacao de dados meteorologicos do INMET (Instituto Nacional de Meteorologia) utilizando Python com integracao direta ao Power BI.

## Objetivo

Consolidar arquivos historicos de temperatura horaria das cidades de Timoteo e Belo Horizonte, realizar a limpeza e padronizacao dos dados, calcular metricas estatisticas descritivas e disponibilizar os resultados para consumo e construcao de dashboards no Power BI.

## Estrutura do Projeto

- `main.py`: Script principal que realiza a leitura dos arquivos CSV no padrao INMET, limpeza dos dados, calculo das estatisticas descritivas, exportacao de tabelas tratadas para o Power BI e geracao de um painel grafico estatico.
- `visual_powerbi.py`: Script configurado para uso direto no componente Visual do Python dentro do Power BI Desktop.
- `dados_temperatura_powerbi.csv`: Base de dados tratada contendo data, cidade e temperatura horaria.
- `resumo_estatistico_powerbi.csv`: Tabela consolidada com as metricas estatisticas de cada cidade.
- `dashboard_powerbi.png`: Painel visual gerado pelo script principal contendo boxplot, histograma com curva de densidade, comparativo de metricas e tabela resumo.

## Metricas Calculadas

Para cada cidade analisada, o projeto calcula:

- Numero de amostras (N)
- Temperatura minima e maxima
- Media, mediana e moda
- Amplitude termica
- Variancia e desvio padrao
- Coeficiente de variacao (CV %)

## Pre-requisitos

Certifique-se de ter o Python instalado juntamente com as bibliotecas abaixo:

```bash
pip install pandas numpy matplotlib seaborn
```

## Como Executar o Projeto Localmente

No terminal, dentro do diretorio do projeto, execute:

```bash
python main.py
```

A execucao exibira o resumo estatistico no terminal e atualizara os arquivos CSV e a imagem do dashboard na pasta do projeto.

## Como Integrar com o Power BI

### 1. Importacao via Arquivos CSV Tratados

1. Abra o Power BI Desktop.
2. Acesse Obter dados e selecione Texto/CSV.
3. Importe os arquivos `dados_temperatura_powerbi.csv` e `resumo_estatistico_powerbi.csv`.

### 2. Importacao Direta via Script do Python

1. No Power BI Desktop, acesse Obter dados, clique em Mais e selecione Script do Python.
2. Insira o script abaixo para carregar os DataFrames processados pelo projeto:

```python
import sys
sys.path.append(r'e:\filli\OneDrive\Documentos\PowerBI e Python')
from main import df_dados, df_estatisticas
```

3. Selecione as tabelas `df_dados` e `df_estatisticas` na janela de navegacao e clique em Carregar.

### 3. Utilizacao do Visual do Python no Relatorio

1. Adicione o elemento Visual do Python (`Py`) ao relatorio do Power BI.
2. Arraste os campos `Cidade` e `Temperatura` da tabela `df_dados` para a area de valores do visual.
3. Cole o conteudo do arquivo `visual_powerbi.py` no editor de script do visual e execute.

