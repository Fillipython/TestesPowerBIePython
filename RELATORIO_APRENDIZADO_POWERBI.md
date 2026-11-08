# Guia Completo e Relatorio Analitico: Modelagem dos Dados do INMET no Power BI

Este documento explica como o Power BI processa, modela em Esquema Estrela (Star Schema), calcula indicadores em DAX e constroi relatorios analiticos utilizando exclusivamente os dados meteorologicos das estacoes do INMET de **Timoteo (Codigo WMO: A511)** e **Belo Horizonte (Codigo WMO: A521)**.

Todos os arquivos modelados para o Power BI estao na pasta `modelo_powerbi/` e os paineis visuais gerados estao na pasta `relatorios/`.

---

## 1. Como o Power BI Trabalha com os Dados do INMET (As 4 Etapas)

1. **ETL no Power Query (Extracao, Transformacao e Carga)**:
   - Os arquivos brutos do INMET possuem um cabecalho institucional nas 8 primeiras linhas (`REGIAO`, `UF`, `ESTACAO`, `CODIGO WMO`, `LATITUDE`, `LONGITUDE`, `ALTITUDE`, `DATA DE FUNDACAO`), seguidos pela tabela separada por `;` e com virgula `,` como separador decimal.
   - No ETL, pulamos as 8 linhas iniciais, convertemos os textos numericos para float, removemos registros de falha de sensor (`<= -100`) e extraímos a hora inteira (`0` a `23`) a partir da coluna `Hora UTC`.
2. **Modelagem Dimensional (Esquema Estrela / Star Schema)**:
   - O Power BI separa os dados das estacoes em **Tabelas Dimensao** (que filtram o relatorio) e **Tabelas Fato** (que guardam as medicoes horarias e diarias):
     - `dim_calendario.csv`: `Data`, `Ano`, `Mes_Num`, `Mes_Nome`, `Dia`, `Dia_Semana` e `Fim_De_Semana`.
     - `dim_estacoes_inmet.csv`: `Codigo_WMO` (`A511`, `A521`), `Cidade` (`Timoteo`, `Belo Horizonte`), `Latitude`, `Longitude` e `Altitude_m` (`300m` em Timoteo vs `915m` em Belo Horizonte).
     - `dim_horario_turno.csv`: `Hora_Dia` (`0` a `23`), `Hora_Formatada`, `Turno` (`Madrugada`, `Manha`, `Tarde`, `Noite`) e `Periodo_Solar` (`Diurno`, `Noturno`).
     - `fato_inmet_horaria.csv`: 4.320 medicoes horarias (2.160 horas de cada cidade) com todas as variaveis meteorologicas do INMET e colunas analiticas dos modelos.
     - `fato_inmet_diaria.csv`: Consolidado diario por estacao (temperaturas minima, media e maxima do dia, amplitude termica diaria, precipitacao acumulada no dia, radiacao total e rajada maxima de vento).
3. **Medidas e Indicadores (DAX vs Python)**:
   - Criacao de metricas dinamicas como Temperatura Media, Sensacao Termica, Amplitude Termica, Media Movel de 24 Horas, Precipitacao Acumulada e Horas de Anomalia Termica.
4. **Relatorios Visuais (Dashboards)**:
   - Construcao de visuais comparativos por estacao, turno do dia, faixas de conforto termico, matriz de correlacao e regressao linear.

---

## 2. Analise Estatistica Multivariada das Variaveis do INMET

A tabela abaixo (exportada em `modelo_powerbi/estatisticas_multivariadas_inmet.csv`) apresenta todas as metricas estatisticas calculadas para as 11 variaveis meteorologicas medidas pelo INMET nas duas cidades (2.160 amostras horarias por estacao):

### 2.1. Estacao Belo Horizonte (A521 - Altitude: 915 m)

| Variavel do INMET | N | Minimo | Maximo | Media | Mediana | Moda | Amplitude | Variancia | Desvio Padrao | CV (%) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Temperatura do Ar (°C) | 2160 | 15,30 | 31,30 | 22,84 | 22,80 | 22,80 | 16,00 | 8,01 | 2,83 | 12,39% |
| Temperatura Maxima Horaria (°C) | 2160 | 16,00 | 32,30 | 23,80 | 23,80 | 23,80 | 16,30 | 8,13 | 2,85 | 11,98% |
| Temperatura Minima Horaria (°C) | 2160 | 14,60 | 30,70 | 21,93 | 21,90 | 21,90 | 16,10 | 8,11 | 2,85 | 12,98% |
| Sensacao Termica (°C) | 2160 | 13,07 | 31,01 | 22,71 | 22,84 | 23,79 | 17,94 | 9,65 | 3,11 | 13,68% |
| Ponto de Orvalho (°C) | 2160 | 10,00 | 20,10 | 15,63 | 15,70 | 15,90 | 10,10 | 2,35 | 1,53 | 9,80% |
| Umidade Relativa (%) | 2160 | 33,00 | 93,00 | 63,96 | 64,00 | 68,00 | 60,00 | 109,41 | 10,46 | 16,35% |
| Pressao Atmosferica (mB) | 2160 | 907,10 | 916,00 | 911,87 | 911,90 | 912,10 | 8,90 | 1,62 | 1,27 | 0,14% |
| Radiacao Global (Kj/m2) | 2160 | 0,00 | 3218,20 | 907,14 | 0,05 | 0,00 | 3218,20 | 1242220,39 | 1114,55 | 122,86% |
| Precipitacao Horaria (mm) | 2160 | 0,00 | 22,10 | 0,19 | 0,00 | 0,00 | 22,10 | 1,85 | 1,36 | 716,57% |
| Velocidade do Vento (m/s) | 2160 | 1,80 | 8,50 | 2,74 | 2,50 | 2,20 | 6,70 | 0,57 | 0,75 | 27,51% |
| Rajada Maxima do Vento (m/s) | 2160 | 3,10 | 10,00 | 5,74 | 5,70 | 6,30 | 6,90 | 1,56 | 1,25 | 21,77% |

### 2.2. Estacao Timoteo (A511 - Altitude: 300 m)

| Variavel do INMET | N | Minimo | Maximo | Media | Mediana | Moda | Amplitude | Variancia | Desvio Padrao | CV (%) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Temperatura do Ar (°C) | 2160 | 18,40 | 34,90 | 26,34 | 26,30 | 25,60 | 16,50 | 10,25 | 3,20 | 12,15% |
| Temperatura Maxima Horaria (°C) | 2160 | 19,30 | 36,40 | 27,29 | 27,20 | 27,20 | 17,10 | 10,34 | 3,22 | 11,79% |
| Temperatura Minima Horaria (°C) | 2160 | 17,60 | 34,10 | 25,46 | 25,40 | 22,50 | 16,50 | 10,41 | 3,23 | 12,67% |
| Sensacao Termica (°C) | 2160 | 17,80 | 37,09 | 27,97 | 28,22 | 27,00 | 19,29 | 13,45 | 3,67 | 13,11% |
| Ponto de Orvalho (°C) | 2160 | 15,00 | 25,50 | 19,97 | 20,00 | 19,80 | 10,50 | 2,61 | 1,62 | 8,09% |
| Umidade Relativa (%) | 2160 | 34,00 | 98,00 | 68,14 | 68,00 | 66,00 | 64,00 | 129,40 | 11,38 | 16,69% |
| Pressao Atmosferica (mB) | 2160 | 1003,40 | 1013,00 | 1008,39 | 1008,40 | 1008,10 | 9,60 | 1,90 | 1,38 | 0,14% |
| Radiacao Global (Kj/m2) | 2160 | 0,00 | 3157,40 | 888,32 | 0,35 | 0,00 | 3157,40 | 1191456,34 | 1091,54 | 122,88% |
| Precipitacao Horaria (mm) | 2160 | 0,00 | 30,50 | 0,32 | 0,00 | 0,00 | 30,50 | 3,32 | 1,82 | 561,11% |
| Velocidade do Vento (m/s) | 2160 | 1,80 | 7,60 | 2,81 | 2,60 | 2,20 | 5,80 | 0,66 | 0,81 | 29,01% |
| Rajada Maxima do Vento (m/s) | 2160 | 3,30 | 10,70 | 5,86 | 5,80 | 5,40 | 7,40 | 1,76 | 1,33 | 22,65% |

---

## 3. Modelos Analiticos Construidos sobre os Dados do INMET

### 3.1. Modelo de Sensacao Termica e Conforto Higrotermico (`Relatorio 1`)
Combinando a **Temperatura do Ar (°C)**, a **Umidade Relativa (%)** e a **Velocidade do Vento (m/s)**, o modelo calcula a **Sensacao Termica Aparente**:
- Em **Timoteo** (altitude 300 m, Vale do Aco), a combinacao de temperatura media de `26,34 °C` com umidade media de `68,14%` eleva a **Sensacao Termica media para `27,97 °C`**, atingindo picos de **`37,09 °C`**.
- Em **Belo Horizonte** (altitude 915 m), a temperatura media e `3,50 °C` mais baixa (`22,84 °C`), e a sensacao termica media fica em **`22,71 °C`**.

### 3.2. Matriz de Correlacao e Modelo de Regressao Linear Multipla (`Relatorio 2`)
A matriz de correlacao (`modelo_powerbi/matriz_correlacao_inmet.csv`) revela como as variaveis fisicas do INMET interagem:
- **Temperatura do Ar vs Umidade Relativa (`r = -0,641`)**: Correlacao negativa forte — conforme a temperatura sobe durante a tarde, a umidade relativa cai acentuadamente.
- **Temperatura do Ar vs Radiacao Global (`r = +0,473`)**: O aquecimento solar diurno impulsiona a elevacao termica.
- **Temperatura do Ar vs Sensacao Termica (`r = +0,972`)** e **Ponto de Orvalho (`r = +0,771`)**: Forte acoplamento termodinamico.
- **Precipitacao vs Velocidade do Vento (`r = +0,314`)**: Eventos de chuva vem acompanhados de aumento nas rajadas de vento.
- **Modelo de Regressao Linear Multipla**: Estima a coluna `Temp_Prevista_Regressao` em funcao de `Umidade_Relativa`, `Radiacao_Global` e `Pressao_Atmosferica`, permitindo identificar no Power BI desvios termicos locais (`Erro_Regressao`).

### 3.3. Pressao Atmosferica (Efeito de Altitude), Chuvas e Anomalias Z-Score (`Relatorio 3`)
- **Impacto da Altitude na Pressao ao Nivel da Estacao**:
  - Como Belo Horizonte esta a **915 m** de altitude, sua pressao atmosferica media ao nivel da estacao e de **`911,87 mB`**, enquanto Timoteo (**300 m** de altitude) registra media de **`1008,39 mB`**.
- **Deteccao de Anomalias Termicas (`|Z-Score| > 2,0`)**:
  - O indicador `Z_Score_Temp` padroniza a temperatura de cada cidade pela sua propria media e desvio padrao, marcando automaticamente como `Anomalia` os horarios que fogem mais de 2 desvios padrao do comportamento normal da estacao.

---

## 4. Formulas DAX para Usar no Power BI com os Dados do INMET

Ao abrir o projeto no Power BI Desktop, voce pode utilizar ou criar estas medidas em DAX na tabela `fato_inmet_horaria`:

### Temperatura Media (°C)
```dax
Temperatura Media = AVERAGE(fato_inmet_horaria[Temperatura_Ar])
```

### Sensacao Termica Media (°C)
```dax
Sensacao Termica Media = AVERAGE(fato_inmet_horaria[Sensacao_Termica])
```

### Amplitude Termica Absoluta (°C)
```dax
Amplitude Termica = MAX(fato_inmet_horaria[Temp_Maxima_Hora]) - MIN(fato_inmet_horaria[Temp_Minima_Hora])
```

### Chuva Acumulada (mm)
```dax
Chuva Acumulada (mm) = SUM(fato_inmet_horaria[Precipitacao_mm])
```

### Umidade Relativa Media (%)
```dax
Umidade Media = AVERAGE(fato_inmet_horaria[Umidade_Relativa])
```

### Total de Horas com Anomalia Termica
```dax
Horas Anomalia Termica = 
CALCULATE(
    COUNTROWS(fato_inmet_horaria),
    fato_inmet_horaria[Anomalia_Termica] = "Anomalia"
)
```

