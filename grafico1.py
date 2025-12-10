import pandas as pd
import matplotlib.pyplot as plt

# --- Tabela 1: interesse por disciplina (usando counter_total e oferta noturna) ---
dados_interesse = []
for disc, qtd in counter_total.items():
    if disc == 'Nenhuma':
        continue
    dados_interesse.append({
        'disciplina': disc,
        'interessados_modelo': qtd,
        'ofertada_BCT_noturno': disc in ucs_bct_night_names
    })

interesse_df = pd.DataFrame(dados_interesse).sort_values(
    'interessados_modelo', ascending=False
).reset_index(drop=True)

print("Tabela 1 – Interesse por disciplina (top 15):")
display(interesse_df.head(15))

# --- Figura 1: Top 10 disciplinas mais demandadas ---
top10 = interesse_df.head(10)

plt.figure(figsize=(8, 4))
plt.bar(top10['disciplina'], top10['interessados_modelo'])
plt.xticks(rotation=45, ha='right')
plt.xlabel('Disciplina')
plt.ylabel('Nº de alunos')
plt.title('Top 10 disciplinas com maior interesse')
plt.tight_layout()
plt.show()
