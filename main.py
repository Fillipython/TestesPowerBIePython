import os
import re
import glob
import zipfile
from datetime import datetime
import requests
import urllib3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

HEADER_LINES = 8
ENCODING = 'latin-1'
DELIMITER = ';'
DECIMAL = ','
PASTA_PADRAO = r'e:\filli\OneDrive\Documentos\PowerBI e Python'
BASE_DIR = PASTA_PADRAO if os.path.exists(PASTA_PADRAO) else (os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else os.getcwd())


def baixar_zip_inmet(ano):
    url = f"https://portal.inmet.gov.br/uploads/dadoshistoricos/{ano}.zip"
    nome_arquivo = os.path.join(BASE_DIR, f"INMET_Historico_{ano}.zip")

    if os.path.exists(nome_arquivo):
        print(f" -> Arquivo {nome_arquivo} já existe localmente. Pulando download.")
        return nome_arquivo

    print(f" -> Baixando dados do Brasil inteiro para o ano de {ano} (~70MB)... Pode demorar um pouco.")

    try:
        resposta = requests.get(url, stream=True, verify=False, timeout=120)

        if resposta.status_code == 200:
            with open(nome_arquivo, 'wb') as f:
                for chunk in resposta.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            print(f" -> Download de {ano} concluído com sucesso!")
            return nome_arquivo
        else:
            print(f" -> Aviso: Não foi possível baixar {ano}. O INMET retornou o código HTTP {resposta.status_code}.")
            return None
    except Exception as e:
        print(f" -> Erro de conexão ao tentar baixar o ano {ano}: {e}")
        return None


def processar_dados_do_zip(caminho_zip, estacoes_alvo):
    lista_dfs = []

    try:
        with zipfile.ZipFile(caminho_zip, 'r') as z:
            arquivos_no_zip = z.namelist()

            for codigo_wmo, nome_cidade in estacoes_alvo.items():
                arquivos_estacao = [f for f in arquivos_no_zip if codigo_wmo in f.upper() and f.upper().endswith('.CSV')]

                if not arquivos_estacao:
                    continue

                arquivo_escolhido = arquivos_estacao[0]
                if len(arquivos_estacao) > 1:
                    def extrair_data_final(nome):
                        match = re.search(r'_(\d{2}-\d{2}-\d{4})\.CSV$', nome.upper())
                        if match:
                            return datetime.strptime(match.group(1), '%d-%m-%Y')
                        return datetime.min
                    arquivo_escolhido = max(arquivos_estacao, key=extrair_data_final)

                nome_final_csv = os.path.join(BASE_DIR, os.path.basename(arquivo_escolhido))
                print(f"    - Extraindo e salvando: {os.path.basename(arquivo_escolhido)}")

                try:
                    with z.open(arquivo_escolhido) as source, open(nome_final_csv, 'wb') as target:
                        target.write(source.read())

                    df = pd.read_csv(nome_final_csv, sep=DELIMITER, encoding=ENCODING,
                                     skiprows=HEADER_LINES, decimal=DECIMAL)
                    df['Cidade'] = nome_cidade
                    lista_dfs.append(df)
                except Exception as e:
                    print(f"    - Erro ao ler CSV de {nome_cidade}: {e}")

    except zipfile.BadZipFile:
        print(f" -> Erro: O arquivo {caminho_zip} está corrompido ou não é um ZIP válido.")

    try:
        if os.path.exists(caminho_zip):
            os.remove(caminho_zip)
            print(f" -> Arquivo {os.path.basename(caminho_zip)} deletado com sucesso para poupar espaço.")
    except Exception as e:
        print(f" -> Aviso: Não foi possível deletar o {caminho_zip}: {e}")

    return lista_dfs


def carregar_csvs_locais_ano(ano, estacoes_alvo):
    lista_dfs = []
    for codigo_wmo, nome_cidade in estacoes_alvo.items():
        padrao = os.path.join(BASE_DIR, f"*{codigo_wmo}*{ano}*.CSV")
        arquivos = glob.glob(padrao)
        if not arquivos:
            return []
        for arq in arquivos:
            df = pd.read_csv(arq, sep=DELIMITER, encoding=ENCODING, skiprows=HEADER_LINES, decimal=DECIMAL)
            df['Cidade'] = nome_cidade
            lista_dfs.append(df)
    return lista_dfs


def preparar_dados_completos():
    anos_para_analisar = [2022, 2023, 2024, 2025, 2026]
    estacoes = {
        'A511': 'Timóteo',
        'A521': 'Belo Horizonte'
    }

    todos_dfs = []

    print("Iniciando a coleta de dados diretamente do portal do INMET...")

    for ano in anos_para_analisar:
        dfs_locais = carregar_csvs_locais_ano(ano, estacoes)
        if dfs_locais:
            print(f"\n[{ano}] -> CSVs locais já extraídos encontrados na pasta.")
            todos_dfs.extend(dfs_locais)
            continue

        print(f"\n[{ano}]")
        caminho_zip = baixar_zip_inmet(ano)

        if caminho_zip:
            dfs_do_ano = processar_dados_do_zip(caminho_zip, estacoes)
            todos_dfs.extend(dfs_do_ano)

    if not todos_dfs:
        raise ValueError("Nenhum dado foi coletado. O site do INMET pode estar fora do ar ou os downloads falharam.")

    print("\nCombinando e limpando todos os dados coletados...")
    df_completo = pd.concat(todos_dfs, ignore_index=True)

    cidades = df_completo['Cidade']
    df_completo.columns = [col.strip().upper() for col in df_completo.columns]
    df_completo['Cidade'] = cidades

    coluna_temp = None
    coluna_data = None
    for col in df_completo.columns:
        if 'TEMPERATURA DO AR' in col and ('BULBO SECO' in col or 'HORARIA' in col):
            coluna_temp = col
        if col.startswith('DATA'):
            coluna_data = col

    if not coluna_temp:
        raise KeyError("Coluna de temperatura não encontrada nos dados baixados.")

    print(f"Utilizando a coluna para análise: {coluna_temp}")

    df_completo[coluna_temp] = pd.to_numeric(df_completo[coluna_temp].astype(str).str.replace(',', '.'), errors='coerce')

    df_limpo = df_completo.dropna(subset=[coluna_temp, 'Cidade']).copy()
    df_limpo = df_limpo[df_limpo[coluna_temp] > -100]

    if coluna_data:
        df_limpo['Data'] = pd.to_datetime(df_limpo[coluna_data], errors='coerce')
        return df_limpo[['Data', 'Cidade', coluna_temp]].rename(columns={coluna_temp: 'Temperatura'})

    return df_limpo[['Cidade', coluna_temp]].rename(columns={coluna_temp: 'Temperatura'})


def calcular_estatisticas(df):
    estatisticas = []
    for cidade in df['Cidade'].unique():
        dados_cidade = df[df['Cidade'] == cidade]['Temperatura']

        media = dados_cidade.mean()
        minimo = dados_cidade.min()
        maximo = dados_cidade.max()

        estatisticas.append({
            'Cidade': cidade,
            'N (Amostras)': int(len(dados_cidade)),
            'Mínimo': round(minimo, 2),
            'Máximo': round(maximo, 2),
            'Média': round(media, 2),
            'Mediana': round(dados_cidade.median(), 2),
            'Moda': round(dados_cidade.mode().iloc[0], 2) if not dados_cidade.mode().empty else np.nan,
            'Amplitude': round(maximo - minimo, 2),
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


def gerar_graficos(df, resumo):
    sns.set_theme(style="whitegrid")
    fig, eixos = plt.subplots(1, 2, figsize=(15, 6))

    sns.boxplot(x='Cidade', y='Temperatura', data=df, ax=eixos[0], hue='Cidade', palette='Set2', legend=False)
    eixos[0].set_title('Boxplot das Temperaturas (2022-2026)')
    eixos[0].set_ylabel('Temperatura (°C)')

    sns.histplot(data=df, x='Temperatura', hue='Cidade', kde=True,
                 element="step", stat="density", common_norm=False, ax=eixos[1], palette='Set2')
    eixos[1].set_title('Distribuição (Histograma) das Temperaturas (2022-2026)')
    eixos[1].set_xlabel('Temperatura (°C)')

    plt.tight_layout()
    caminho_site = os.path.join(BASE_DIR, 'graficos_temperatura_site.png')
    plt.savefig(caminho_site, dpi=150)
    plt.close(fig)
    print("\nGráficos gerados com sucesso! Salvos como 'graficos_temperatura_site.png'")


def main():
    try:
        df = preparar_dados_completos()
        resumo = calcular_estatisticas(df)
        exportar_para_powerbi(df, resumo)

        print("\n\nTABELA RESUMO DAS ESTATÍSTICAS (TEMPERATURA HORÁRIA 2022-2026)")
        print(resumo.to_string(index=False))

        print("\nVALORES EXTREMOS POR CIDADE:")
        for _, row in resumo.iterrows():
            print(f"{row['Cidade']}:")
            print(f"  Temperatura Mínima: {row['Mínimo']}°C")
            print(f"  Temperatura Máxima: {row['Máximo']}°C")

        gerar_graficos(df, resumo)

    except Exception as e:
        print(f"\n[ERRO CRÍTICO] O programa parou. Motivo: {e}")


if __name__ == "__main__":
    main()
