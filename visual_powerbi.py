import matplotlib.pyplot as plt
import seaborn as sns

sns.set_theme(style='whitegrid')
fig, axes = plt.subplots(1, 2, figsize=(12, 5))

paleta = {'Timóteo': '#E63946', 'Belo Horizonte': '#1D3557'}

sns.boxplot(
    data=dataset,
    x='Cidade',
    y='Temperatura',
    hue='Cidade',
    palette=paleta,
    legend=False,
    ax=axes[0]
)
axes[0].set_title('Distribuição de Temperatura por Cidade')
axes[0].set_ylabel('Temperatura (°C)')

sns.kdeplot(
    data=dataset,
    x='Temperatura',
    hue='Cidade',
    fill=True,
    palette=paleta,
    ax=axes[1]
)
axes[1].set_title('Densidade de Temperatura (°C)')
axes[1].set_xlabel('Temperatura (°C)')

plt.tight_layout()
plt.show()

