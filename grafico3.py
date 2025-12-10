import matplotlib.pyplot as plt
import numpy as np

def plot_satisfacao_e_tabela(sat_df, save_path=None):
    """
    Figura 7 – Distribuição da satisfação dos estudantes.
    Tabela 3 – Estatísticas descritivas da satisfação (%).
    Usa sat_df['satisfacao'] entre 0 e 1.
    """
    vals = sat_df['satisfacao'].dropna() * 100  # converte para %

    # ---------- Figura 7: histograma ----------
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.hist(vals, bins=10)  # cores padrão
    ax.set_xlabel('Satisfação (%)')
    ax.set_ylabel('Número de estudantes')
    ax.set_title('Distribuição da satisfação dos estudantes')
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, format='png')  # Salva a figura no caminho desejado
        print(f"Figura salva em: {save_path}")
    plt.show()

# Exemplo de chamada:
plot_satisfacao_e_tabela(sat_df, save_path='/content/distribuicao_satisfacao.png')
