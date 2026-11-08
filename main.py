import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import glob

HEADER_LINES = 8
ENCODING = 'latin-1'
DELIMITER = ';'
DECIMAL = ','


def carregar_dados_cidade(cidade_nome, padrao_arquivo):
    arquivos = glob.glob(padrao_arquivo)
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
    padrao_timoteo = '*TIMOTEO*.CSV'
    padrao_bh = '*BELO HORIZONTE*.CSV'

    df_timoteo = carregar_dados_cidade('Timóteo', padrao_timoteo)
    df_bh = carregar_dados_cidade('Belo Horizonte', padrao_bh)
    df_completo = pd.concat([df_timoteo, df_bh], ignore_index=True)

    cidades = df_completo['Cidade']
    df_completo.columns = [col.strip().upper() for col in df_completo.columns]
    df_completo['Cidade'] = cidades

    coluna_temp = None
    for col in df_completo.columns:
        if 'TEMPERATURA DO AR' in col:
            coluna_temp = col
            break

    df_completo[coluna_temp] = pd.to_numeric(df_completo[coluna_temp].astype(str).str.replace(',', '.'), errors='coerce')
    df_limpo = df_completo.dropna(subset=[coluna_temp, 'Cidade']).copy()
    df_limpo = df_limpo[df_limpo[coluna_temp] > -100]

    return df_limpo[['Cidade', coluna_temp]].rename(columns={coluna_temp: 'Temperatura'})


def calcular_estatisticas(df):
    estatisticas = []
    for cidade in df['Cidade'].unique():
        dados_cidade = df[df['Cidade'] == cidade]['Temperatura']

        media = dados_cidade.mean()
        estatisticas.append({
            'Cidade': cidade,
            'N (Amostras)': len(dados_cidade),
            'Mínimo': dados_cidade.min(),
            'Máximo': dados_cidade.max(),
            'Média': media,
            'Mediana': dados_cidade.median(),
            'Moda': dados_cidade.mode().iloc[0] if not dados_cidade.mode().empty else np.nan,
            'Amplitude': dados_cidade.max() - dados_cidade.min(),
            'Variância': dados_cidade.var(),
            'Desvio Padrão': dados_cidade.std(),
            'CV (%)': (dados_cidade.std() / media) * 100 if media != 0 else np.nan
        })
    return pd.DataFrame(estatisticas)


def main():
    df = preparar_dados()
    resumo_estatistico = calcular_estatisticas(df)
    print(resumo_estatistico.to_string(index=False))


if __name__ == "__main__":
    main()

