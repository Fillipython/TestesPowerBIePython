# Guia Completo e Relatorio Analitico: Modelagem dos Dados Historicos do INMET (2022-2026) no Power BI

Este documento explica como o Power BI processa, modela em Esquema Estrela (Star Schema), calcula indicadores em DAX e constroi relatorios analiticos utilizando os dados historicos oficiais baixados diretamente do portal do INMET (2022 a 2026) das estacoes de **Timoteo (Codigo WMO: A511)** e **Belo Horizonte - Pampulha (Codigo WMO: A521)**, totalizando **80.844 medicoes horarias reais**.

Todos os arquivos modelados para o Power BI estao na pasta `modelo_powerbi/` e os paineis visuais gerados estao na pasta `relatorios/`.

---

## 1. Como o Power BI Trabalha com os Dados do INMET (As 4 Etapas)

1. **ETL no Power Query (Extracao, Transformacao e Carga)**:
   - Os 10 arquivos CSV extraidos dos pacotes anuais do INMET (2022 a 2026 para `A511` e `A521`) possuem cabecalho institucional nas 8 primeiras linhas (`REGIAO`, `UF`, `ESTACAO`, `CODIGO WMO`, `LATITUDE`, `LONGITUDE`, `ALTITUDE`, `DATA DE FUNDACAO`), seguidos pela tabela separada por `;` e com virgula `,` como separador decimal.
   - No ETL, pulamos as 8 linhas iniciais, padronizamos os nomes das colunas (que variam entre anos com ou sem acento no INMET), convertemos textos numericos para float e removemos falhas de sensor (`<= -100` ou `-9999`).
2. **Modelagem Dimensional (Esquema Estrela / Star Schema)**:
   - O Power BI separa os dados das estacoes em **Tabelas Dimensao** (que filtram o relatorio) e **Tabelas Fato** (que guardam as medicoes horarias e diarias):
     - `dim_calendario.csv`: `Data`, `Ano` (`2022` a `2026`), `Mes_Num`, `Mes_Nome`, `Dia`, `Dia_Semana` e `Fim_De_Semana`.
     - `dim_estacoes_inmet.csv`: `Codigo_WMO` (`A511`, `A521`), `Cidade` (`Timoteo`, `Belo Horizonte`), `Latitude`, `Longitude` e `Altitude_m`.
     - `dim_horario_turno.csv`: `Hora_Dia` (`0` a `23`), `Hora_Formatada`, `Turno` (`Madrugada`, `Manha`, `Tarde`, `Noite`) e `Periodo_Solar` (`Diurno`, `Noturno`).
     - `fato_inmet_horaria.csv`: **80.844 medicoes horarias reais** (`38.508` de Timoteo e `42.336` de Belo Horizonte) com todas as variaveis meteorologicas do INMET e colunas analiticas dos modelos.
     - `fato_inmet_diaria.csv`: Consolidado diario de 2022 a 2026 por estacao (temperaturas minima, media e maxima do dia, amplitude termica diaria, precipitacao acumulada no dia, radiacao total e rajada maxima de vento).
3. **Medidas e Indicadores (DAX vs Python)**:
   - Criacao de metricas dinamicas como Temperatura Media, Sensacao Termica, Amplitude Termica, Media Movel, Precipitacao Acumulada e Horas de Anomalia Termica.
4. **Relatorios Visuais (Dashboards)**:
   - Construcao de visuais comparativos da serie historica 2022-2026 por estacao, turno do dia, faixas de conforto termico, matriz de correlacao e regressao linear.

---

## 2. Analise Estatistica Multivariada dos Dados Reais do INMET (2022-2026)

A tabela abaixo (exportada em `modelo_powerbi/estatisticas_multivariadas_inmet.csv`) apresenta todas as metricas estatisticas reais de 2022 a 2026 para as 11 variaveis meteorologicas medidas pelo INMET nas duas cidades:

### 2.1. Estacao Belo Horizonte - Pampulha (A521: 42.336 medicoes horarias)

| Variavel do INMET (2022-2026) | N (Amostras) | Minimo | Maximo | Media | Mediana | Moda | Amplitude | Variancia | Desvio Padrao | CV (%) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Temperatura do Ar (°C) | 42.336 | 6,80 | 37,60 | 22,10 | 21,70 | 20,40 | 30,80 | 17,71 | 4,21 | 19,04% |
| Temperatura Maxima Horaria (°C) | 42.332 | 7,20 | 38,60 | 22,83 | 22,30 | 20,80 | 31,40 | 19,45 | 4,41 | 19,32% |
| Temperatura Minima Horaria (°C) | 42.332 | 6,40 | 36,30 | 21,40 | 21,10 | 19,80 | 29,90 | 15,88 | 3,99 | 18,62% |
| Sensacao Termica (°C) | 42.336 | 3,57 | 38,01 | 22,73 | 22,77 | 22,44 | 34,44 | 20,61 | 4,54 | 19,97% |
| Ponto de Orvalho (°C) | 42.336 | -5,40 | 23,10 | 14,63 | 15,30 | 17,90 | 28,50 | 13,72 | 3,70 | 25,32% |
| Umidade Relativa (%) | 42.336 | 10,00 | 93,00 | 65,52 | 67,00 | 92,00 | 83,00 | 319,51 | 17,87 | 27,28% |
| Pressao Atmosferica (mB) | 42.336 | 906,20 | 930,20 | 919,47 | 919,30 | 918,60 | 24,00 | 9,98 | 3,16 | 0,34% |
| Radiacao Global (Kj/m2) | 42.336 | 0,00 | 4298,60 | 726,11 | 23,70 | 0,00 | 4298,60 | 1051700,68 | 1025,52 | 141,23% |
| Precipitacao Horaria (mm) | 42.336 | 0,00 | 65,00 | 0,17 | 0,00 | 0,00 | 65,00 | 1,98 | 1,41 | 850,11% |
| Velocidade do Vento (m/s) | 42.334 | 0,00 | 7,10 | 1,41 | 1,40 | 0,00 | 7,10 | 0,72 | 0,85 | 60,00% |
| Rajada Maxima do Vento (m/s) | 42.331 | 0,00 | 24,20 | 4,62 | 4,60 | 4,60 | 24,20 | 4,47 | 2,11 | 45,73% |

### 2.2. Estacao Timoteo (A511: 38.508 medicoes horarias)

| Variavel do INMET (2022-2026) | N (Amostras) | Minimo | Maximo | Media | Mediana | Moda | Amplitude | Variancia | Desvio Padrao | CV (%) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Temperatura do Ar (°C) | 38.508 | 9,30 | 36,10 | 22,78 | 22,50 | 21,30 | 26,80 | 15,09 | 3,88 | 17,05% |
| Temperatura Maxima Horaria (°C) | 38.503 | 9,70 | 36,20 | 23,43 | 23,10 | 22,60 | 26,50 | 16,04 | 4,01 | 17,09% |
| Temperatura Minima Horaria (°C) | 38.503 | 9,10 | 35,00 | 22,17 | 21,90 | 21,10 | 25,90 | 14,09 | 3,75 | 16,93% |
| Sensacao Termica (°C) | 38.508 | 8,54 | 40,04 | 24,92 | 24,86 | 25,92 | 31,50 | 21,48 | 4,63 | 18,60% |
| Ponto de Orvalho (°C) | 38.508 | -1,50 | 27,30 | 17,14 | 17,60 | 19,30 | 28,80 | 12,29 | 3,51 | 20,46% |
| Umidade Relativa (%) | 38.508 | 21,00 | 100,00 | 72,35 | 74,00 | 79,00 | 79,00 | 231,90 | 15,23 | 21,05% |
| Pressao Atmosferica (mB) | 38.508 | 946,50 | 972,20 | 960,19 | 960,00 | 959,00 | 25,70 | 13,31 | 3,65 | 0,38% |
| Radiacao Global (Kj/m2) | 38.508 | 0,00 | 5197,30 | 630,81 | 0,40 | 0,00 | 5197,30 | 1076859,80 | 1037,72 | 164,51% |
| Precipitacao Horaria (mm) | 38.508 | 0,00 | 53,20 | 0,18 | 0,00 | 0,00 | 53,20 | 2,03 | 1,42 | 807,57% |
| Velocidade do Vento (m/s) | 38.505 | 0,00 | 4,80 | 0,60 | 0,40 | 0,00 | 4,80 | 0,41 | 0,64 | 106,63% |
| Rajada Maxima do Vento (m/s) | 38.502 | 0,00 | 16,80 | 3,05 | 3,10 | 0,00 | 16,80 | 4,32 | 2,08 | 68,03% |

---

## 3. Principais Descobertas nos Dados Reais do INMET (2022-2026)

### 3.1. Comparativo Termico e Sensacao Termica (`Relatorio 1`)
- **Média e Mediana mais altas em Timoteo**: Timoteo registra media de **`22,78 °C`** (mediana `22,50 °C`), enquanto Belo Horizonte registra media de **`22,10 °C`** (mediana `21,70 °C`).
- **Maior Amplitude Termica em Belo Horizonte**: No periodo 2022-2026, Belo Horizonte registrou tanto o frio mais intenso (**`6,80 °C`**) quanto o pico absoluto de calor seco (**`37,60 °C`**, amplitude de `30,80 °C` e CV de `19,04%`), enquanto Timoteo variou entre **`9,30 °C`** e **`36,10 °C`** (amplitude de `26,80 °C` e CV de `17,05%`).
- **Sensacao Termica em Timoteo chega a `40,04 °C`**: Como Timoteo possui umidade relativa media maior (`72,35%` contra `65,52%` em BH) e menor velocidade media de vento (`0,60 m/s` contra `1,41 m/s` em BH), a **Sensacao Termica media de Timoteo e `2,19 °C` superior** (`24,92 °C` em Timoteo vs `22,73 °C` em BH), atingindo pico de **`40,04 °C`**!

### 3.2. Matriz de Correlacao e Modelo de Regressao Linear Multipla (`Relatorio 2`)
A matriz de correlacao real de 2022 a 2026 (`modelo_powerbi/matriz_correlacao_inmet.csv`) comprova as relacoes fisicas entre as variaveis do INMET:
- **Temperatura do Ar vs Radiacao Solar Global (`r = +0,619`)**: Forte correlacao positiva — a radiacao solar e o principal motor da elevacao da temperatura horaria.
- **Temperatura do Ar vs Umidade Relativa (`r = -0,585`)**: Forte correlacao negativa — nos horarios e dias mais quentes, a umidade relativa cai drasticamente (chegando a `10%` em BH).
- **Temperatura do Ar vs Sensacao Termica (`r = +0,940`)**: Altissima correlacao direta.
- **Pressao Atmosferica vs Velocidade do Vento (`r = -0,453`)**: Quedas de pressao atmosferica estao associadas ao aumento da circulacao de ventos.

### 3.3. Pressao Atmosferica, Precipitacao Anual e Extremos (`Relatorio 3`)
- **Pressao Atmosferica por Estacao**: A estacao de Belo Horizonte opera na faixa de `906,2 a 930,2 mB` (media `919,47 mB`), enquanto a estacao de Timoteo opera na faixa de `946,5 a 972,2 mB` (media `960,19 mB`).
- **Extremos de Chuva Horaria e Ventania**: Belo Horizonte registrou pancada maxima horaria de **`65,0 mm`** e rajada de vento de **`24,2 m/s` (`87,1 km/h`)**, enquanto Timoteo registrou pancada maxima horaria de **`53,2 mm`** e rajada de **`16,8 m/s` (`60,5 km/h`)**.

---

## 4. Formulas DAX para Usar no Power BI com os Dados do INMET

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
