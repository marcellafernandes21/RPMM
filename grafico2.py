# Tabela 2 – já veio do modelo como tabela_turmas_df
print("Tabela 2 – Turmas abertas por disciplina:")
display(tabela_turmas_df)

# Figura 3 – número de turmas por letra (cada turma conta uma vez)
turmas_por_letra = grade_df[['disciplina', 'turma', 'letra']].drop_duplicates()
contagem_letra = turmas_por_letra['letra'].value_counts().sort_index()

plt.figure(figsize=(6, 4))
plt.bar(contagem_letra.index, contagem_letra.values)
plt.xlabel('Letra')
plt.ylabel('Número de turmas')
plt.title('Distribuição de turmas por letra')
plt.tight_layout()
plt.show()

print("Número de turmas por letra:")
display(contagem_letra.to_frame(name='num_turmas'))
