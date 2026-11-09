# TestesPowerBIePython

Projeto de processamento, modelagem dimensional (Star Schema), analise estatistica multivariada, regressao linear e visualizacao de dados meteorologicos do INMET (Instituto Nacional de Meteorologia) utilizando Python com integracao direta ao Power BI.

## Visao do Painel no Power BI Desktop

Abaixo esta a captura do painel gerado no Power BI Desktop com os dados do INMET:

![Painel Power BI Desktop](print_powerbi_dashboard.png)

O relatorio contem cartoes de indicadores (KPIs), filtro de cidades, graficos de colunas agrupadas por turno, ciclo horario das temperaturas, amplitude termica por faixa de conforto e grafico de area da sensacao termica horaria.

## Objetivo

Consolidar todas as variaveis meteorologicas horarias das estacoes do INMET de Timoteo (A511) e Belo Horizonte (A521), realizar a limpeza e padronizacao dos dados, construir um Esquema Estrela completo para o Power BI, calcular estatisticas descritivas e modelos de regressao/correlacao, e gerar paineis analiticos de referencia.

## Variaveis do INMET Analisadas

- Temperatura do Ar - Bulbo Seco Horaria (°C)
- Temperatura Maxima e Minima na Hora Anterior (°C)
- Temperatura do Ponto de Orvalho (°C)
- Sensacao Termica Calculada (°C)
- Umidade Relativa do Ar Horaria (%)
- Pressao Atmosferica ao Nivel da Estacao (mB)
- Radiacao Global (Kj/m2)
- Precipitacao Total Horaria (mm)
- Velocidade e Rajada Maxima do Vento (m/s) e Direcao (graus)

## Estrutura do Projeto

- `main.py`: Script de leitura dos arquivos CSV no padrao INMET, limpeza dos dados, calculo das estatisticas de temperatura e geracao do painel inicial (`dashboard_powerbi.png`).
- `modelos_powerbi.py`: Script de modelagem dimensional e analitica do INMET que gera o Esquema Estrela (`dim_calendario`, `dim_estacoes_inmet`, `dim_horario_turno`, `fato_inmet_horaria`, `fato_inmet_diaria`), a tabela de estatisticas multivariadas, a matriz de correlacao, o modelo de regressao linear e os tres relatorios visuais na pasta `relatorios/`.
- `visual_powerbi.py`: Script para uso direto no componente Visual do Python dentro do Power BI Desktop.
- `PainelPowerBI.pbip`: Arquivo de projeto nativo para abrir o relatorio pronto diretamente no Power BI Desktop.
- `print_powerbi_dashboard.png`: Captura do painel em execucao dentro da interface do Power BI Desktop.
- `RELATORIO_APRENDIZADO_POWERBI.md`: Guia didatico e relatorio analitico detalhando todos os resultados das estacoes do INMET e as formulas DAX equivalentes para uso no Power BI.
- `modelo_powerbi/`: Pasta contendo as tabelas Fato e Dimensao do INMET prontas para importacao no Power BI Desktop.
- `relatorios/`: Pasta com os tres dashboards meteorologicos gerados a partir dos dados do INMET.

## Pre-requisitos

```bash
pip install pandas numpy matplotlib seaborn
```

## Como Executar

Para rodar o resumo estatistico de temperatura e gerar o dashboard inicial:

```bash
python main.py
```

Para construir o Esquema Estrela completo do INMET, os modelos de correlacao/regressao e os tres relatorios analiticos:

```bash
python modelos_powerbi.py
```

## Como Integrar com o Power BI

### 1. Abrindo Direto pelo Projeto Power BI (.pbip)

1. Dê dois cliques no arquivo `PainelPowerBI.pbip`.
2. O Power BI Desktop abrira com todas as tabelas, relacionamentos e visuais configurados.

### 2. Importando o Esquema Estrela do INMET (`modelo_powerbi/`)

1. Abra o Power BI Desktop.
2. Acesse Obter dados e selecione Texto/CSV.
3. Importe as tabelas da pasta `modelo_powerbi/`:
   - `dim_calendario.csv`
   - `dim_estacoes_inmet.csv`
   - `dim_horario_turno.csv`
   - `fato_inmet_horaria.csv`
   - `fato_inmet_diaria.csv`
   - `estatisticas_multivariadas_inmet.csv`
   - `matriz_correlacao_inmet.csv`
4. Na guia Exibicao de Modelo do Power BI, relacione `dim_calendario[Data]`, `dim_estacoes_inmet[Codigo_WMO]` e `dim_horario_turno[Hora_Dia]` com a tabela `fato_inmet_horaria`.

### 3. Importacao Direta via Script do Python

No Power BI Desktop, acesse Obter dados -> Mais -> Script do Python e utilize:

```python
import sys
sys.path.append(r'e:\filli\OneDrive\Documentos\PowerBI e Python')
from modelos_powerbi import (
    dim_calendario,
    dim_estacoes,
    dim_horario_turno,
    fato_inmet_horaria,
    fato_inmet_diaria,
    estatisticas_multivariadas,
    matriz_correlacao
)
```
