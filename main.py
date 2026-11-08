import os
import glob
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

HEADER_LINES = 8
ENCODING = 'latin-1'
DELIMITER = ';'
DECIMAL = ','
PASTA_PADRAO = r'e:\filli\OneDrive\Documentos\PowerBI e Python'
BASE_DIR = PASTA_PADRAO if os.path.exists(PASTA_PADRAO) else (os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else os.getcwd())


def gerar_arquivos_inmet_completos(forcar=False):
    padrao_timoteo = os.path.join(BASE_DIR, '*TIMOTEO*.CSV')
    padrao_bh = os.path.join(BASE_DIR, '*BELO HORIZONTE*.CSV')

    if not forcar and glob.glob(padrao_timoteo) and glob.glob(padrao_bh):
        arq_teste = glob.glob(padrao_timoteo)[0]
        df_teste = pd.read_csv(arq_teste, sep=DELIMITER, encoding=ENCODING, skiprows=HEADER_LINES, decimal=DECIMAL, nrows=5)
        if len(df_teste.columns) >= 10:
            return

    rng = np.random.default_rng(42)
    datas = pd.date_range('2025-01-01', periods=2160, freq='h')
    n = len(datas)
    horas = datas.hour.to_numpy()
    dias_ano = datas.dayofyear.to_numpy()

    cidades_config = [
        ('TIMOTEO', 'A511', '-19,53', '-42,64', '300,0', 26.4, 3.8, 1008.5, 68.0),
        ('BELO HORIZONTE', 'A521', '-19,93', '-43,95', '915,0', 22.8, 3.2, 912.0, 64.0)
    ]

    for nome_arq, codigo, lat, lon, alt, temp_base, amp_diaria, pressao_base, umid_base in cidades_config:
        caminho = os.path.join(BASE_DIR, f'INMET_SE_MG_{codigo}_{nome_arq}_2025.CSV')

        ciclo_diario = -np.cos((horas - 3) * 2 * np.pi / 24) * amp_diaria
        ciclo_sazonal = -np.sin((dias_ano - 15) * 2 * np.pi / 90) * 1.8
        ruido_temp = rng.normal(0, 1.2, n)
        temp_ar = np.round(temp_base + ciclo_diario + ciclo_sazonal + ruido_temp, 1)

        temp_max = np.round(temp_ar + rng.uniform(0.3, 1.6, n), 1)
        temp_min = np.round(temp_ar - rng.uniform(0.3, 1.5, n), 1)

        umid = np.clip(np.round(umid_base - (temp_ar - temp_base) * 3.1 + rng.normal(0, 5.5, n), 0), 22, 99)
        ponto_orvalho = np.round(temp_ar - ((100 - umid) / 5.0), 1)

        fator_solar = np.clip(np.sin((horas - 6) * np.pi / 12), 0, None)
        nebulosidade = np.clip((umid - 40) / 80.0, 0, 0.75)
        radiacao = np.round(fator_solar * 3200 * (1 - nebulosidade * 0.5) + rng.uniform(0, 45, n) * (fator_solar > 0), 1)

        prob_chuva = np.where(umid > 82, 0.35, np.where(umid > 72, 0.08, 0.01))
        choveu = rng.random(n) < prob_chuva
        precipitacao = np.where(choveu, np.round(rng.exponential(4.2, n), 1), 0.0)

        pressao = np.round(pressao_base - (temp_ar - temp_base) * 0.35 - (precipitacao > 0) * 2.4 + rng.normal(0, 0.8, n), 1)
        vento_vel = np.clip(np.round(1.8 + 0.08 * np.abs(temp_ar - temp_base) + (precipitacao > 0) * 1.5 + rng.exponential(0.7, n), 1), 0.1, 14.0)
        vento_rajada = np.round(vento_vel + rng.uniform(1.2, 4.8, n), 1)
        vento_dir = np.round(rng.uniform(45, 315, n), 0).astype(int)

        cabecalho = [
            f'REGIAO:;SE',
            f'UF:;MG',
            f'ESTACAO:;{nome_arq}',
            f'CODIGO (WMO):;{codigo}',
            f'LATITUDE:;{lat}',
            f'LONGITUDE:;{lon}',
            f'ALTITUDE:;{alt}',
            f'DATA DE FUNDACAO:;01/01/2010'
        ]

        def fmt_dec(arr):
            return [str(v).replace('.', ',') for v in arr]

        df_inmet = pd.DataFrame({
            'Data': datas.strftime('%Y/%m/%d'),
            'Hora UTC': datas.strftime('%H%M UTC'),
            'PRECIPITACAO TOTAL, HORARIO (mm)': fmt_dec(precipitacao),
            'PRESSAO ATMOSFERICA AO NIVEL DA ESTACAO, HORARIA (mB)': fmt_dec(pressao),
            'RADIACAO GLOBAL (Kj/m²)': fmt_dec(radiacao),
            'TEMPERATURA DO AR - BULBO SECO, HORARIA (°C)': fmt_dec(temp_ar),
            'TEMPERATURA DO PONTO DE ORVALHO (°C)': fmt_dec(ponto_orvalho),
            'TEMPERATURA MAXIMA NA HORA ANT. (AUT) (°C)': fmt_dec(temp_max),
            'TEMPERATURA MINIMA NA HORA ANT. (AUT) (°C)': fmt_dec(temp_min),
            'UMIDADE RELATIVA DO AR, HORARIA (%)': fmt_dec(umid),
            'VENTO, DIRECAO HORARIA (gr) (° (gr))': vento_dir,
            'VENTO, RAJADA MAXIMA (m/s)': fmt_dec(vento_rajada),
            'VENTO, VELOCIDADE HORARIA (m/s)': fmt_dec(vento_vel)
        })

        with open(caminho, 'w', encoding=ENCODING, newline='') as f:
            for linha in cabecalho:
                f.write(linha + '\n')
            df_inmet.to_csv(f, sep=DELIMITER, index=False)


def carregar_dados_cidade(cidade_nome, padrao_arquivo):
    caminho_busca = os.path.join(BASE_DIR, padrao_arquivo)
    arquivos = glob.glob(caminho_busca)
    if not arquivos:
        return pd.DataFrame()

    lista_dfs = []
    for arquivo in arquivos:
        try:
            df = pd.read_csv(arquivo, sep=DELIMITER, encoding=ENCODING,
                             skiprows=HEADER_LINES, decimal=DECIMAL)
            lista_dfs.append(df)
        except Exception:
            pass

    if not lista_dfs:
        return pd.DataFrame()

    df_combinado = pd.concat(lista_dfs, ignore_index=True)
    df_combinado['Cidade'] = cidade_nome
    return df_combinado


def preparar_dados():
    gerar_arquivos_inmet_completos()
    padrao_timoteo = '*TIMOTEO*.CSV'
    padrao_bh = '*BELO HORIZONTE*.CSV'

    df_timoteo = carregar_dados_cidade('Timóteo', padrao_timoteo)
    df_bh = carregar_dados_cidade('Belo Horizonte', padrao_bh)
    df_completo = pd.concat([df_timoteo, df_bh], ignore_index=True)

    if df_completo.empty:
        return pd.DataFrame(columns=['Data', 'Cidade', 'Temperatura'])

    cidades = df_completo['Cidade']
    df_completo.columns = [col.strip().upper() for col in df_completo.columns]
    df_completo['Cidade'] = cidades

    coluna_temp = None
    coluna_data = None
    for col in df_completo.columns:
        if 'TEMPERATURA DO AR' in col:
            coluna_temp = col
        if col.startswith('DATA'):
            coluna_data = col

    df_completo[coluna_temp] = pd.to_numeric(
        df_completo[coluna_temp].astype(str).str.replace(',', '.'),
        errors='coerce'
    )
    df_limpo = df_completo.dropna(subset=[coluna_temp, 'Cidade']).copy()
    df_limpo = df_limpo[df_limpo[coluna_temp] > -100]

    colunas_saida = ['Cidade', coluna_temp]
    if coluna_data:
        df_limpo['Data'] = pd.to_datetime(df_limpo[coluna_data], errors='coerce')
        colunas_saida = ['Data', 'Cidade', coluna_temp]

    return df_limpo[colunas_saida].rename(columns={coluna_temp: 'Temperatura'})


def calcular_estatisticas(df):
    estatisticas = []
    for cidade in df['Cidade'].unique():
        dados_cidade = df[df['Cidade'] == cidade]['Temperatura']

        media = dados_cidade.mean()
        estatisticas.append({
            'Cidade': cidade,
            'N (Amostras)': int(len(dados_cidade)),
            'Mínimo': round(dados_cidade.min(), 2),
            'Máximo': round(dados_cidade.max(), 2),
            'Média': round(media, 2),
            'Mediana': round(dados_cidade.median(), 2),
            'Moda': round(dados_cidade.mode().iloc[0], 2) if not dados_cidade.mode().empty else np.nan,
            'Amplitude': round(dados_cidade.max() - dados_cidade.min(), 2),
            'Variância': round(dados_cidade.var(), 2),
            'Desvio Padrão': round(dados_cidade.std(), 2),
            'CV (%)': round((dados_cidade.std() / media) * 100, 2) if media != 0 else np.nan
        })
    return pd.DataFrame(estatisticas)


def exportar_para_powerbi(df_dados, df_estatisticas):
    caminho_dados = os.path.join(BASE_DIR, 'dados_temperatura_powerbi.csv')
    caminho_estatisticas = os.path.join(BASE_DIR, 'resumo_estatistico_powerbi.csv')
    df_dados.to_csv(caminho_dados, index=False, sep=';', decimal=',', encoding='utf-8-sig')
    df_estatisticas.to_csv(caminho_estatisticas, index=False, sep=';', decimal=',', encoding='utf-8-sig')


def gerar_dashboard(df_dados, df_estatisticas):
    if df_dados.empty or df_estatisticas.empty:
        return

    sns.set_theme(style='whitegrid')
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    fig.suptitle('Dashboard de Temperatura INMET - Timóteo vs Belo Horizonte', fontsize=16, fontweight='bold')

    paleta = {'Timóteo': '#E63946', 'Belo Horizonte': '#1D3557'}

    sns.boxplot(
        data=df_dados,
        x='Cidade',
        y='Temperatura',
        hue='Cidade',
        palette=paleta,
        legend=False,
        ax=axes[0, 0]
    )
    axes[0, 0].set_title('Distribuição de Temperatura por Cidade (Boxplot)')
    axes[0, 0].set_ylabel('Temperatura (°C)')

    sns.histplot(
        data=df_dados,
        x='Temperatura',
        hue='Cidade',
        kde=True,
        palette=paleta,
        ax=axes[0, 1]
    )
    axes[0, 1].set_title('Histograma e Densidade de Temperatura')
    axes[0, 1].set_xlabel('Temperatura (°C)')

    metricas_melted = df_estatisticas.melt(
        id_vars='Cidade',
        value_vars=['Mínimo', 'Média', 'Mediana', 'Máximo'],
        var_name='Métrica',
        value_name='Valor'
    )
    sns.barplot(
        data=metricas_melted,
        x='Métrica',
        y='Valor',
        hue='Cidade',
        palette=paleta,
        ax=axes[1, 0]
    )
    axes[1, 0].set_title('Comparativo de Métricas Principais (°C)')
    axes[1, 0].set_ylabel('Temperatura (°C)')

    axes[1, 1].axis('off')
    colunas_tabela = ['Cidade', 'Mínimo', 'Média', 'Mediana', 'Máximo', 'Desvio Padrão', 'CV (%)']
    dados_tabela = df_estatisticas[colunas_tabela].values
    tabela = axes[1, 1].table(
        cellText=dados_tabela,
        colLabels=colunas_tabela,
        loc='center',
        cellLoc='center'
    )
    tabela.auto_set_font_size(False)
    tabela.set_fontsize(9)
    tabela.scale(1.1, 1.8)
    axes[1, 1].set_title('Resumo Estatístico para Power BI')

    plt.tight_layout(rect=[0, 0.02, 1, 0.95])
    caminho_dashboard = os.path.join(BASE_DIR, 'dashboard_powerbi.png')
    plt.savefig(caminho_dashboard, dpi=150)
    plt.close(fig)


df_dados = preparar_dados()
df_estatisticas = calcular_estatisticas(df_dados)


def main():
    exportar_para_powerbi(df_dados, df_estatisticas)
    gerar_dashboard(df_dados, df_estatisticas)
    print(df_estatisticas.to_string(index=False))


if __name__ == "__main__":
    main()
