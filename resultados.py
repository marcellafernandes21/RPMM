# Diagnóstico detalhado por disciplina (execute onde o solver já rodou)
import pandas as pd
from collections import defaultdict

diag = []

# map de disciplina -> lista de candidatos (índices) com W>0
for c, nome in enumerate(disciplinas):
    # interessados do formulário
    int_form = int(counter_total.get(nome, 0))
    
    # candidatos com W>0
    candidatos = [s for s in range(n_students) if W[s, c] > 0]
    n_cand = len(candidatos)
    
    # alunos únicos disponíveis em qualquer letra (usando avail_letter)
    dispon_any = set(s for s in candidatos if any(avail_letter[s, li] == 1 for li in range(n_letters)))
    n_dispon_any = len(dispon_any)
    
    # disponibilidade por letra (apenas entre candidatos)
    dispon_por_letra = {L: int(sum(avail_letter[s, li] for s in candidatos)) for li, L in enumerate(letters)}
    
    # open_disc valores
    open_vals = [int(solver.Value(open_disc[(c, k)])) for k in range(MAX_TURMAS_POR_DISC)]
    
    # quantos foram alocados na disciplina
    alocados = []
    for k in range(MAX_TURMAS_POR_DISC):
        for s in candidatos:
            if (s, c, k) in x and solver.Value(x[(s, c, k)]) == 1:
                alocados.append((s, k + 1))
    
    # ver onde os candidatos foram alocados (outras disciplinas)
    alocacoes_candidatos = []
    for s in candidatos:
        aloc = []
        for c2, nome2 in enumerate(disciplinas):
            for k2 in range(MAX_TURMAS_POR_DISC):
                if (s, c2, k2) in x and solver.Value(x[(s, c2, k2)]) == 1:
                    aloc.append((nome2, k2 + 1))
        alocacoes_candidatos.append((s, df_bct.loc[s, 'email'] if 'email' in df_bct.columns else s, W[s, c], aloc))
    
    # soma total de pesos possível para essa disciplina (soma W dos candidatos)
    soma_W = int(sum(W[s, c] for s in candidatos))
    
    diag.append({
        'disciplina': nome,
        'interessados_form': int_form,
        'candidatos_W>0': n_cand,
        'dispon_any_uniques': n_dispon_any,
        **{f'dispon_{L}': dispon_por_letra[L] for L in letters},
        'open_t1': open_vals[0] if len(open_vals) > 0 else 0,
        'open_t2': open_vals[1] if len(open_vals) > 1 else 0,
        'alocados_total_na_disc': len(alocados),
        'soma_W_candidatos': soma_W,
        'ex_alocados_exemplo': ','.join(f"{s}-{k}" for s, k in alocados[:20])
    })

diag_df = pd.DataFrame(diag).sort_values(['open_t1', 'open_t2', 'disciplina'])
pd.set_option('display.max_rows', None)
print("=== Diagnóstico resumo por disciplina ===")
display(diag_df)

# Mostrar detalhes dos candidatos que ficaram sem turma em qualquer disciplina
# Para cada disciplina, verificamos se algum candidato não foi alocado

details = {}
for c, nome in enumerate(disciplinas):
    candidatos = [s for s in range(n_students) if W[s, c] > 0]
    alunos_sem_turma = []
    
    for s in candidatos:
        alocado = False
        for k in range(MAX_TURMAS_POR_DISC):
            if (s, c, k) in x and solver.Value(x[(s, c, k)]) == 1:
                alocado = True
                break
        
        if not alocado:  # se o aluno não foi alocado
            email = df_bct.loc[s, 'email'] if 'email' in df_bct.columns else s
            pesos = int(W[s, c])
            dispon_letters = [letters[li] for li in range(n_letters) if avail_letter[s, li] == 1]
            aloc = []  # Não foi alocado, então lista vazia
            alunos_sem_turma.append({
                's': s, 
                'email': email, 
                'peso_W': pesos, 
                'dispon_letters': ','.join(dispon_letters), 
                'alocacoes': ';'.join([f"{n}-{t}" for n, t in aloc])
            })
    
    if alunos_sem_turma:
        details[nome] = pd.DataFrame(alunos_sem_turma).sort_values('peso_W', ascending=False).reset_index(drop=True)
        print(f"\n--- Detalhes dos alunos que não foram alocados para a disciplina: {nome} ---")
        display(details[nome])

