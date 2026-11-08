import os
import glob
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from main import gerar_arquivos_inmet_completos, HEADER_LINES, ENCODING, DELIMITER, DECIMAL, BASE_DIR

PASTA_MODELO = os.path.join(BASE_DIR, 'modelo_powerbi')
PASTA_RELATORIOS = os.path.join(BASE_DIR, 'relatorios')

os.makedirs(PASTA_MODELO, exist_ok=True)
os.makedirs(PASTA_RELATORIOS, exist_ok=True)


def carregar_base_completa_inmet():
    gerar_arquivos_inmet_completos()
    padroes = [
        ('Timóteo', 'A511', '*TIMOTEO*.CSV'),
        ('Belo Horizonte', 'A521', '*BELO HORIZONTE*.CSV')
    ]

    lista_dfs = []
    for cidade, codigo, padrao in padroes:
        arquivos = glob.glob(os.path.join(BASE_DIR, padrao))
        for arq in arquivos:
            df = pd.read_csv(arq, sep=DELIMITER, encoding=ENCODING, skiprows=HEADER_LINES, decimal=DECIMAL)
            df['Cidade'] = cidade
            df['Codigo_WMO'] = codigo
            lista_dfs.append(df)

    df_raw = pd.concat(lista_dfs, ignore_index=True)

    mapa_colunas = {}
    for col in df_raw.columns:
        c_up = col.strip().upper()
        if c_up.startswith('DATA'):
            mapa_colunas[col] = 'Data'
        elif 'HORA' in c_up and 'TEMP' not in c_up and 'VENTO' not in c_up and 'PRECIP' not in c_up and 'PRESSAO' not in c_up and 'UMIDADE' not in c_up:
            mapa_colunas[col] = 'Hora_UTC'
        elif 'PRECIPITACAO' in c_up:
            mapa_colunas[col] = 'Precipitacao_mm'
        elif 'PRESSAO ATMOSFERICA' in c_up:
            mapa_colunas[col] = 'Pressao_Atmosferica'
        elif 'RADIACAO' in c_up:
            mapa_colunas[col] = 'Radiacao_Global'
        elif 'TEMPERATURA DO AR' in c_up:
            mapa_colunas[col] = 'Temperatura_Ar'
        elif 'PONTO DE ORVALHO' in c_up:
            mapa_colunas[col] = 'Ponto_Orvalho'
        elif 'TEMPERATURA MAXIMA' in c_up:
            mapa_colunas[col] = 'Temp_Maxima_Hora'
        elif 'TEMPERATURA MINIMA' in c_up:
            mapa_colunas[col] = 'Temp_Minima_Hora'
        elif 'UMIDADE RELATIVA' in c_up:
            mapa_colunas[col] = 'Umidade_Relativa'
        elif 'DIRECAO' in c_up:
            mapa_colunas[col] = 'Direcao_Vento'
        elif 'RAJADA' in c_up:
            mapa_colunas[col] = 'Rajada_Vento'
        elif 'VELOCIDADE' in c_up:
            mapa_colunas[col] = 'Velocidade_Vento'

    df = df_raw.rename(columns=mapa_colunas).copy()
    df['Data'] = pd.to_datetime(df['Data'], errors='coerce')
    df['Hora_Dia'] = df['Hora_UTC'].astype(str).str.extract(r'(\d{2})')[0].astype(int)

    colunas_numericas = [
        'Precipitacao_mm', 'Pressao_Atmosferica', 'Radiacao_Global',
        'Temperatura_Ar', 'Ponto_Orvalho', 'Temp_Maxima_Hora',
        'Temp_Minima_Hora', 'Umidade_Relativa', 'Direcao_Vento',
        'Rajada_Vento', 'Velocidade_Vento'
    ]
    for col in colunas_numericas:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '.'), errors='coerce')

    df = df.dropna(subset=['Data', 'Cidade', 'Temperatura_Ar']).copy()
    df = df[df['Temperatura_Ar'] > -100].sort_values(['Cidade', 'Data', 'Hora_Dia']).reset_index(drop=True)
    return df


def construir_esquema_estrela_inmet(df):
    datas_unicas = pd.DataFrame({'Data': sorted(df['Data'].unique())})
    datas_unicas['Ano'] = datas_unicas['Data'].dt.year
    datas_unicas['Mes_Num'] = datas_unicas['Data'].dt.month
    nomes_meses = {1: 'Janeiro', 2: 'Fevereiro', 3: 'Marco', 4: 'Abril', 5: 'Maio', 6: 'Junho',
                   7: 'Julho', 8: 'Agosto', 9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'}
    datas_unicas['Mes_Nome'] = datas_unicas['Mes_Num'].map(nomes_meses)
    datas_unicas['Dia'] = datas_unicas['Data'].dt.day
    nomes_semana = {0: 'Segunda', 1: 'Terca', 2: 'Quarta', 3: 'Quinta', 4: 'Sexta', 5: 'Sabado', 6: 'Domingo'}
    datas_unicas['Dia_Semana'] = datas_unicas['Data'].dt.dayofweek.map(nomes_semana)
    datas_unicas['Fim_De_Semana'] = datas_unicas['Data'].dt.dayofweek.isin([5, 6]).map({True: 'Sim', False: 'Nao'})

    dim_estacoes = pd.DataFrame({
        'Codigo_WMO': ['A511', 'A521'],
        'Cidade': ['Timóteo', 'Belo Horizonte'],
        'Regiao': ['SE', 'SE'],
        'UF': ['MG', 'MG'],
        'Latitude': [-19.53, -19.93],
        'Longitude': [-42.64, -43.95],
        'Altitude_m': [300.0, 915.0]
    })

    horas_unicas = pd.DataFrame({'Hora_Dia': list(range(24))})
    horas_unicas['Hora_Formatada'] = horas_unicas['Hora_Dia'].apply(lambda h: f'{h:02d}:00')
    cond_turno = [
        horas_unicas['Hora_Dia'].between(0, 5),
        horas_unicas['Hora_Dia'].between(6, 11),
        horas_unicas['Hora_Dia'].between(12, 17)
    ]
    escolhas_turno = ['1. Madrugada (00h-05h)', '2. Manha (06h-11h)', '3. Tarde (12h-17h)']
    horas_unicas['Turno'] = np.select(cond_turno, escolhas_turno, default='4. Noite (18h-23h)')
    horas_unicas['Periodo_Solar'] = np.where(horas_unicas['Hora_Dia'].between(6, 17), 'Diurno', 'Noturno')

    fato_horaria = df.merge(horas_unicas[['Hora_Dia', 'Turno', 'Periodo_Solar']], on='Hora_Dia', how='left')
    fato_horaria = fato_horaria.sort_values(['Cidade', 'Data', 'Hora_Dia']).reset_index(drop=True)
    fato_horaria['Indice_Hora'] = fato_horaria.groupby('Cidade').cumcount()
    fato_horaria['Amplitude_Horaria'] = (fato_horaria['Temp_Maxima_Hora'] - fato_horaria['Temp_Minima_Hora']).round(2)

    t = fato_horaria['Temperatura_Ar']
    u = fato_horaria['Umidade_Relativa']
    sensacao = t + 0.33 * ((u / 100.0) * 6.105 * np.exp((17.27 * t) / (237.7 + t))) - 0.70 * fato_horaria['Velocidade_Vento'] - 4.00
    fato_horaria['Sensacao_Termica'] = sensacao.round(2)

    fato_horaria['Media_Movel_24h'] = (
        fato_horaria.groupby('Cidade')['Temperatura_Ar']
        .transform(lambda s: s.rolling(24, min_periods=1).mean())
        .round(2)
    )

    media_cid = fato_horaria.groupby('Cidade')['Temperatura_Ar'].transform('mean')
    std_cid = fato_horaria.groupby('Cidade')['Temperatura_Ar'].transform('std')
    fato_horaria['Z_Score_Temp'] = ((fato_horaria['Temperatura_Ar'] - media_cid) / std_cid).round(2)
    fato_horaria['Anomalia_Termica'] = np.where(fato_horaria['Z_Score_Temp'].abs() > 2.0, 'Anomalia', 'Normal')

    cond_faixa = [
        fato_horaria['Temperatura_Ar'] < 18.0,
        fato_horaria['Temperatura_Ar'].between(18.0, 26.0),
        fato_horaria['Temperatura_Ar'].between(26.01, 31.0)
    ]
    faixas = ['Ameno (<18C)', 'Confortavel (18C-26C)', 'Quente (26C-31C)']
    fato_horaria['Faixa_Conforto'] = np.select(cond_faixa, faixas, default='Muito Quente (>31C)')

    cond_chuva = [
        fato_horaria['Precipitacao_mm'] == 0,
        fato_horaria['Precipitacao_mm'].between(0.1, 2.5),
        fato_horaria['Precipitacao_mm'].between(2.51, 10.0)
    ]
    classes_chuva = ['Sem Chuva', 'Chuva Fraca', 'Chuva Moderada']
    fato_horaria['Classificacao_Chuva'] = np.select(cond_chuva, classes_chuva, default='Chuva Forte')

    fato_horaria['Temp_Prevista_Regressao'] = np.nan
    for cidade in fato_horaria['Cidade'].unique():
        mask = fato_horaria['Cidade'] == cidade
        sub = fato_horaria.loc[mask]
        X = np.column_stack([
            np.ones(len(sub)),
            sub['Umidade_Relativa'].to_numpy(),
            sub['Radiacao_Global'].to_numpy(),
            sub['Pressao_Atmosferica'].to_numpy()
        ])
        y = sub['Temperatura_Ar'].to_numpy()
        betas, _, _, _ = np.linalg.lstsq(X, y, rcond=None)
        fato_horaria.loc[mask, 'Temp_Prevista_Regressao'] = np.round(X @ betas, 2)

    fato_horaria['Erro_Regressao'] = (fato_horaria['Temperatura_Ar'] - fato_horaria['Temp_Prevista_Regressao']).round(2)

    fato_diaria = fato_horaria.groupby(['Data', 'Codigo_WMO', 'Cidade'], as_index=False).agg(
        Temp_Min_Dia=('Temp_Minima_Hora', 'min'),
        Temp_Media_Dia=('Temperatura_Ar', 'mean'),
        Temp_Max_Dia=('Temp_Maxima_Hora', 'max'),
        Sensacao_Media_Dia=('Sensacao_Termica', 'mean'),
        Umidade_Media_Dia=('Umidade_Relativa', 'mean'),
        Pressao_Media_Dia=('Pressao_Atmosferica', 'mean'),
        Chuva_Total_Dia_mm=('Precipitacao_mm', 'sum'),
        Radiacao_Total_Dia=('Radiacao_Global', 'sum'),
        Vento_Medio_Dia=('Velocidade_Vento', 'mean'),
        Rajada_Max_Dia=('Rajada_Vento', 'max')
    )
    fato_diaria['Amplitude_Diaria'] = (fato_diaria['Temp_Max_Dia'] - fato_diaria['Temp_Min_Dia']).round(2)
    fato_diaria['Dia_Com_Chuva'] = np.where(fato_diaria['Chuva_Total_Dia_mm'] > 0, 'Sim', 'Nao')

    for col in ['Temp_Min_Dia', 'Temp_Media_Dia', 'Temp_Max_Dia', 'Sensacao_Media_Dia',
                'Umidade_Media_Dia', 'Pressao_Media_Dia', 'Chuva_Total_Dia_mm',
                'Radiacao_Total_Dia', 'Vento_Medio_Dia', 'Rajada_Max_Dia']:
        fato_diaria[col] = fato_diaria[col].round(2)

    datas_unicas.to_csv(os.path.join(PASTA_MODELO, 'dim_calendario.csv'), index=False, sep=';', decimal=',', encoding='utf-8-sig')
    dim_estacoes.to_csv(os.path.join(PASTA_MODELO, 'dim_estacoes_inmet.csv'), index=False, sep=';', decimal=',', encoding='utf-8-sig')
    horas_unicas.to_csv(os.path.join(PASTA_MODELO, 'dim_horario_turno.csv'), index=False, sep=';', decimal=',', encoding='utf-8-sig')
    fato_horaria.to_csv(os.path.join(PASTA_MODELO, 'fato_inmet_horaria.csv'), index=False, sep=';', decimal=',', encoding='utf-8-sig')
    fato_diaria.to_csv(os.path.join(PASTA_MODELO, 'fato_inmet_diaria.csv'), index=False, sep=';', decimal=',', encoding='utf-8-sig')

    return datas_unicas, dim_estacoes, horas_unicas, fato_horaria, fato_diaria


def calcular_estatisticas_multivariadas_inmet(fato_horaria):
    variaveis = [
        ('Temperatura_Ar', 'Temperatura do Ar (°C)'),
        ('Temp_Maxima_Hora', 'Temperatura Maxima Horaria (°C)'),
        ('Temp_Minima_Hora', 'Temperatura Minima Horaria (°C)'),
        ('Sensacao_Termica', 'Sensacao Termica (°C)'),
        ('Ponto_Orvalho', 'Ponto de Orvalho (°C)'),
        ('Umidade_Relativa', 'Umidade Relativa (%)'),
        ('Pressao_Atmosferica', 'Pressao Atmosferica (mB)'),
        ('Radiacao_Global', 'Radiacao Global (Kj/m2)'),
        ('Precipitacao_mm', 'Precipitacao Horaria (mm)'),
        ('Velocidade_Vento', 'Velocidade do Vento (m/s)'),
        ('Rajada_Vento', 'Rajada Maxima do Vento (m/s)')
    ]

    linhas = []
    for cidade in fato_horaria['Cidade'].unique():
        sub = fato_horaria[fato_horaria['Cidade'] == cidade]
        for col, nome_var in variaveis:
            serie = sub[col].dropna()
            media = serie.mean()
            linhas.append({
                'Cidade': cidade,
                'Variavel': nome_var,
                'N_Amostras': int(len(serie)),
                'Minimo': round(serie.min(), 2),
                'Maximo': round(serie.max(), 2),
                'Media': round(media, 2),
                'Mediana': round(serie.median(), 2),
                'Moda': round(serie.mode().iloc[0], 2) if not serie.mode().empty else np.nan,
                'Amplitude': round(serie.max() - serie.min(), 2),
                'Variancia': round(serie.var(), 2),
                'Desvio_Padrao': round(serie.std(), 2),
                'CV_Pct': round((serie.std() / media) * 100, 2) if media != 0 else np.nan
            })

    df_est = pd.DataFrame(linhas)
    df_est.to_csv(os.path.join(PASTA_MODELO, 'estatisticas_multivariadas_inmet.csv'), index=False, sep=';', decimal=',', encoding='utf-8-sig')

    cols_corr = ['Temperatura_Ar', 'Sensacao_Termica', 'Ponto_Orvalho', 'Umidade_Relativa',
                 'Pressao_Atmosferica', 'Radiacao_Global', 'Precipitacao_mm', 'Velocidade_Vento']
    df_corr = fato_horaria[cols_corr].corr().round(3).reset_index().rename(columns={'index': 'Variavel'})
    df_corr.to_csv(os.path.join(PASTA_MODELO, 'matriz_correlacao_inmet.csv'), index=False, sep=';', decimal=',', encoding='utf-8-sig')

    return df_est, df_corr


def gerar_relatorio_01_perfil_termico(fato_horaria):
    sns.set_theme(style='whitegrid')
    fig, axes = plt.subplots(2, 2, figsize=(16, 10))
    fig.suptitle('Relatorio 1 (INMET Power BI): Perfil Termico, Turnos e Conforto - Timoteo vs Belo Horizonte', fontsize=15, fontweight='bold')

    paleta = {'Timóteo': '#E63946', 'Belo Horizonte': '#1D3557'}

    sns.lineplot(
        data=fato_horaria,
        x='Indice_Hora',
        y='Media_Movel_24h',
        hue='Cidade',
        palette=paleta,
        linewidth=2,
        ax=axes[0, 0]
    )
    axes[0, 0].set_title('Tendencia da Temperatura: Media Movel de 24 Horas (°C)')
    axes[0, 0].set_xlabel('Horas Acumuladas no Periodo')
    axes[0, 0].set_ylabel('Temperatura Media 24h (°C)')

    perfil_horario = fato_horaria.groupby(['Cidade', 'Hora_Dia'], as_index=False)['Temperatura_Ar'].mean()
    sns.lineplot(
        data=perfil_horario,
        x='Hora_Dia',
        y='Temperatura_Ar',
        hue='Cidade',
        palette=paleta,
        marker='o',
        linewidth=2.5,
        ax=axes[0, 1]
    )
    axes[0, 1].set_title('Ciclo Diario Medio de Temperatura por Hora (00h as 23h UTC)')
    axes[0, 1].set_xlabel('Hora do Dia (UTC)')
    axes[0, 1].set_ylabel('Temperatura Media (°C)')
    axes[0, 1].set_xticks(range(0, 24, 2))

    ordem_turnos = ['1. Madrugada (00h-05h)', '2. Manha (06h-11h)', '3. Tarde (12h-17h)', '4. Noite (18h-23h)']
    sns.boxplot(
        data=fato_horaria,
        x='Turno',
        y='Temperatura_Ar',
        hue='Cidade',
        order=ordem_turnos,
        palette=paleta,
        ax=axes[1, 0]
    )
    axes[1, 0].set_title('Distribuicao de Temperatura por Turno do Dia')
    axes[1, 0].set_xlabel('Turno')
    axes[1, 0].set_ylabel('Temperatura (°C)')

    contagem_faixas = fato_horaria.groupby(['Cidade', 'Faixa_Conforto']).size().reset_index(name='Total_Horas')
    ordem_faixas = ['Ameno (<18C)', 'Confortavel (18C-26C)', 'Quente (26C-31C)', 'Muito Quente (>31C)']
    sns.barplot(
        data=contagem_faixas,
        x='Faixa_Conforto',
        y='Total_Horas',
        hue='Cidade',
        order=ordem_faixas,
        palette=paleta,
        ax=axes[1, 1]
    )
    axes[1, 1].set_title('Quantidade de Horas por Faixa de Conforto Termico')
    axes[1, 1].set_xlabel('Faixa de Conforto')
    axes[1, 1].set_ylabel('Horas Registradas')

    plt.tight_layout(rect=[0, 0.02, 1, 0.95])
    plt.savefig(os.path.join(PASTA_RELATORIOS, 'relatorio_01_perfil_termico_inmet.png'), dpi=150)
    plt.close(fig)


def gerar_relatorio_02_correlacao_regressao(fato_horaria):
    sns.set_theme(style='whitegrid')
    fig, axes = plt.subplots(2, 2, figsize=(16, 11))
    fig.suptitle('Relatorio 2 (INMET Power BI): Correlacao Meteorologica, Regressao e Sensacao Termica', fontsize=15, fontweight='bold')

    paleta = {'Timóteo': '#E63946', 'Belo Horizonte': '#1D3557'}

    cols_corr = ['Temperatura_Ar', 'Sensacao_Termica', 'Ponto_Orvalho', 'Umidade_Relativa',
                 'Pressao_Atmosferica', 'Radiacao_Global', 'Precipitacao_mm', 'Velocidade_Vento']
    matriz = fato_horaria[cols_corr].corr()
    sns.heatmap(
        matriz,
        annot=True,
        fmt='.2f',
        cmap='coolwarm',
        vmin=-1,
        vmax=1,
        ax=axes[0, 0]
    )
    axes[0, 0].set_title('Matriz de Correlacao de Pearson das Variaveis do INMET')

    amostra = fato_horaria.sample(n=min(800, len(fato_horaria)), random_state=42)
    sns.scatterplot(
        data=amostra,
        x='Umidade_Relativa',
        y='Temperatura_Ar',
        hue='Cidade',
        palette=paleta,
        alpha=0.5,
        ax=axes[0, 1]
    )
    for cidade, cor in paleta.items():
        sub = fato_horaria[fato_horaria['Cidade'] == cidade]
        sns.regplot(
            data=sub,
            x='Umidade_Relativa',
            y='Temperatura_Ar',
            scatter=False,
            color=cor,
            ax=axes[0, 1]
        )
    axes[0, 1].set_title('Regressao Linear: Temperatura do Ar vs Umidade Relativa (%)')
    axes[0, 1].set_xlabel('Umidade Relativa (%)')
    axes[0, 1].set_ylabel('Temperatura do Ar (°C)')

    sns.scatterplot(
        data=amostra,
        x='Temperatura_Ar',
        y='Temp_Prevista_Regressao',
        hue='Cidade',
        palette=paleta,
        alpha=0.5,
        ax=axes[1, 0]
    )
    lim_min = fato_horaria['Temperatura_Ar'].min()
    lim_max = fato_horaria['Temperatura_Ar'].max()
    axes[1, 0].plot([lim_min, lim_max], [lim_min, lim_max], 'k--', linewidth=2, label='Ideal (Real = Previsto)')
    axes[1, 0].set_title('Modelo Preditivo Multiplo: Temperatura Real vs Prevista')
    axes[1, 0].set_xlabel('Temperatura Real (°C)')
    axes[1, 0].set_ylabel('Temperatura Prevista pelo Modelo (°C)')
    axes[1, 0].legend()

    rad_horaria = fato_horaria.groupby(['Cidade', 'Hora_Dia'], as_index=False)['Radiacao_Global'].mean()
    sns.barplot(
        data=rad_horaria[rad_horaria['Hora_Dia'].between(6, 18)],
        x='Hora_Dia',
        y='Radiacao_Global',
        hue='Cidade',
        palette=paleta,
        ax=axes[1, 1]
    )
    axes[1, 1].set_title('Radiacao Solar Global Media por Hora Diurna (Kj/m2)')
    axes[1, 1].set_xlabel('Hora do Dia (UTC)')
    axes[1, 1].set_ylabel('Radiacao Media (Kj/m2)')

    plt.tight_layout(rect=[0, 0.02, 1, 0.95])
    plt.savefig(os.path.join(PASTA_RELATORIOS, 'relatorio_02_correlacao_e_regressao_inmet.png'), dpi=150)
    plt.close(fig)


def gerar_relatorio_03_chuva_pressao_extremos(fato_horaria, fato_diaria):
    sns.set_theme(style='whitegrid')
    fig, axes = plt.subplots(2, 2, figsize=(16, 10))
    fig.suptitle('Relatorio 3 (INMET Power BI): Precipitacao, Pressao Atmosferica, Ventos e Anomalias', fontsize=15, fontweight='bold')

    paleta = {'Timóteo': '#E63946', 'Belo Horizonte': '#1D3557'}

    fato_diaria['Mes'] = fato_diaria['Data'].dt.strftime('%Y-%m')
    chuva_mensal = fato_diaria.groupby(['Cidade', 'Mes'], as_index=False)['Chuva_Total_Dia_mm'].sum()
    sns.barplot(
        data=chuva_mensal,
        x='Mes',
        y='Chuva_Total_Dia_mm',
        hue='Cidade',
        palette=paleta,
        ax=axes[0, 0]
    )
    axes[0, 0].set_title('Precipitacao Acumulada Mensal por Cidade (mm)')
    axes[0, 0].set_xlabel('Ano-Mes')
    axes[0, 0].set_ylabel('Chuva Acumulada (mm)')

    sns.kdeplot(
        data=fato_horaria,
        x='Pressao_Atmosferica',
        hue='Cidade',
        fill=True,
        palette=paleta,
        ax=axes[0, 1]
    )
    axes[0, 1].set_title('Distribuicao da Pressao Atmosferica (Impacto da Altitude: 300m vs 915m)')
    axes[0, 1].set_xlabel('Pressao Atmosferica ao Nivel da Estacao (mB)')
    axes[0, 1].set_ylabel('Densidade')

    sns.boxplot(
        data=fato_horaria,
        x='Cidade',
        y='Rajada_Vento',
        hue='Classificacao_Chuva',
        palette='viridis',
        ax=axes[1, 0]
    )
    axes[1, 0].set_title('Rajada Maxima de Vento (m/s) por Intensidade de Chuva')
    axes[1, 0].set_xlabel('Cidade')
    axes[1, 0].set_ylabel('Rajada de Vento (m/s)')

    anomalias = fato_horaria[fato_horaria['Anomalia_Termica'] == 'Anomalia']
    sns.scatterplot(
        data=fato_horaria,
        x='Indice_Hora',
        y='Temperatura_Ar',
        hue='Cidade',
        palette=paleta,
        alpha=0.2,
        s=18,
        ax=axes[1, 1]
    )
    sns.scatterplot(
        data=anomalias,
        x='Indice_Hora',
        y='Temperatura_Ar',
        color='#FFB703',
        edgecolor='black',
        s=60,
        label='Anomalia (|Z| > 2)',
        ax=axes[1, 1]
    )
    axes[1, 1].set_title('Deteccao de Anomalias Termicas no INMET (|Z-Score| > 2)')
    axes[1, 1].set_xlabel('Horas Acumuladas')
    axes[1, 1].set_ylabel('Temperatura do Ar (°C)')

    plt.tight_layout(rect=[0, 0.02, 1, 0.95])
    plt.savefig(os.path.join(PASTA_RELATORIOS, 'relatorio_03_chuva_pressao_e_vento_inmet.png'), dpi=150)
    plt.close(fig)


df_inmet_completo = carregar_base_completa_inmet()
dim_calendario, dim_estacoes, dim_horario_turno, fato_inmet_horaria, fato_inmet_diaria = construir_esquema_estrela_inmet(df_inmet_completo)
estatisticas_multivariadas, matriz_correlacao = calcular_estatisticas_multivariadas_inmet(fato_inmet_horaria)


def main():
    gerar_relatorio_01_perfil_termico(fato_inmet_horaria)
    gerar_relatorio_02_correlacao_regressao(fato_inmet_horaria)
    gerar_relatorio_03_chuva_pressao_extremos(fato_inmet_horaria, fato_inmet_diaria)

    print('=== ESTATISTICAS MULTIVARIADAS DO INMET (TIMOTEO E BELO HORIZONTE) ===')
    print(estatisticas_multivariadas.to_string(index=False))
    print('\n=== MATRIZ DE CORRELACAO METEOROLOGICA DO INMET ===')
    print(matriz_correlacao.to_string(index=False))


if __name__ == '__main__':
    main()

