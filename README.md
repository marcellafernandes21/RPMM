# RPMM
# Otimização da Oferta de Disciplinas - BCT Noturno UNIFESP

## 📋 Descrição
Este trabalho foi desenvolvido como parte da disciplina Resolução de Problemas via Modelagem Matemática na Universidade Federal de São Paulo (UNIFESP) - Instituto de Ciência e Tecnologia, campus São José dos Campos.
# Modelo BCT Noturno com letras A–E fixas

Cada disciplina aberta escolhe **exatamente uma letra (A–E)** e cada letra tem 2 horários fixos na semana, na grade:

|        | Seg | Ter | Qua | Qui | Sex |
|--------|-----|-----|-----|-----|-----|
| 19–21h |  A  |  C  |  E  |  B  |  D  |
| 21–23h |  B  |  D  |  A  |  C  |  E  |

O modelo decide quais disciplinas abrir, qual letra usar e quais alunos cursam cada disciplina.

## 👥 Autores
- Eduardo Lopes Arrais de Oliveira (RA: 168804)
- João Henrique Oliveira Medina (RA: 168876)
- Marcella Fernandes Moraes (RA: 170982)

## Orientadores
Prof. Dr. Luiz Leduino de Salles Neto
Prof. Dr. Luiz Felipe Bueno

## Licença
Uso acadêmico - UNIFESP 2025

## 🎯 Objetivos
Maximizar satisfação dos estudantes respeitando:
- Grade horária fixa (letras A-E)
- Capacidade de turmas (3-5 alunos-unidade)
- Disponibilidade individual
- Limite de 5 disciplinas/aluno

## ▶️ Como Executar

### 1. Upload dos Arquivos
```python
# Faça upload:
# - respostas_formulario.xlsx
# - Planilha Departamento 2025.xlsx
```

### 2. Execute o Notebook
```bash
from pathlib import Path
import pandas as pd
import numpy as np
import json
import ast
from collections import Counter
import matplotlib.pyplot as plt
from ortools.sat.python import cp_model

# -----------------------------
# 1) Caminhos dos arquivos
# -----------------------------

FORM_PATH = Path('Dados de entrada/respostas_formulario.xlsx')
ATRIB_PATH = Path('Dados de entrada/Planilha de Atribuição Didática para o Departamento 2025.xlsx')

assert FORM_PATH.exists(), f'Arquivo não encontrado em {FORM_PATH}.'
assert ATRIB_PATH.exists(), f'Arquivo não encontrado em {ATRIB_PATH}.'

print('FORM_PATH =', FORM_PATH)
print('ATRIB_PATH =', ATRIB_PATH)

# -----------------------------
# 2) Leitura do formulário (interesses)
# -----------------------------
df = pd.read_excel(FORM_PATH)
print('Linhas no formulário:', len(df))
print(df.head())

# Constantes de horário do formulário
DIAS = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado']
FAIXAS_NOTURNO = ['19h00 - 21h00', '21h00 - 23h00']

def parse_list_safe(text):
    if pd.isna(text):
        return []
    try:
        return ast.literal_eval(text)
    except Exception:
        return []

def slots_from_json(horario_str):
    if pd.isna(horario_str):
        return []
    dados = json.loads(horario_str)
    slots = []
    for bloco in dados:
        time = bloco['time']
        if time not in FAIXAS_NOTURNO:
            continue
        for dia in DIAS:
            if bloco.get(dia):
                slots.append((dia, time))
    return slots

# Filtra só alunos BCIT
df_bct = df[df['curso_atual'] == 'BCIT'].reset_index(drop=True)
print('Alunos BCIT:', len(df_bct))

# Contagem de interesse nas disciplinas
counter_total = Counter()
for _, row in df_bct.iterrows():
    for col in ['disciplinas_semestre_par','disciplinas_semestre_impar','disciplinas_interesse']:
        if col in df_bct.columns:
            counter_total.update(parse_list_safe(row[col]))

print('Total de disciplinas citadas no formulário:', len(counter_total))
# -----------------------------
# 3) Leitura da planilha de oferta 
# -----------------------------
df_ucs = pd.read_excel(ATRIB_PATH, sheet_name='UCs_x_Docentes')

mask_night = df_ucs['TURMA'].astype(str).str.contains('N', na=False)

df_bct_noturno_oferta = df_ucs[mask_night].copy()
ucs_bct_night_names = set(
    df_bct_noturno_oferta['UNIDADE CURRICULAR']
    .dropna()
    .astype(str)
)

print('Disciplinas ofertadas para BCT noturno (planilha 2):', len(ucs_bct_night_names))
print(sorted(list(ucs_bct_night_names))[:20])

# -----------------------------
# 4) Seleção das disciplinas do modelo
# -----------------------------
# Critérios:
#  - aparece no formulário (counter_total)
#  - aparece na oferta BCT noturno (ucs_bct_night_names)
#  - tem pelo menos 5 interessados (escala: 5 ~ 50 alunos)
#  - não é "Nenhuma"
MIN_ALUNOS_DISC = 5

disciplinas = sorted([
    d for d, cnt in counter_total.items()
    if d != 'Nenhuma'
    and d in ucs_bct_night_names
    and cnt >= MIN_ALUNOS_DISC
])

disc_index = {d: i for i, d in enumerate(disciplinas)}
n_disc = len(disciplinas)

print('Disciplinas usadas no modelo (BCT noturno + >=5 interessados):', n_disc)
print(disciplinas)

# -----------------------------
# 5) Matriz de pesos W (aluno x disciplina)
# -----------------------------
n_students = len(df_bct)
W = np.zeros((n_students, n_disc), dtype=int)

for s_idx, row in df_bct.iterrows():
    par   = set(parse_list_safe(row.get('disciplinas_semestre_par')))
    impar = set(parse_list_safe(row.get('disciplinas_semestre_impar')))
    inter = set(parse_list_safe(row.get('disciplinas_interesse')))
    for d in disciplinas:
        w = 0
        if d in par or d in impar:
            w += 2
        if d in inter:
            w += 1
        # bonus se o aluno é noturno
        if str(row.get('turno','')).lower() == 'noturno':
            w = int(round(1.5 * w))
        W[s_idx, disc_index[d]] = w

print('Pares aluno-disciplina com peso>0:', int((W > 0).sum()))
# -----------------------------
# 6) Grade fixa com letras A–E
# -----------------------------
DIAS_GRADE   = ['Segunda','Terça','Quarta','Quinta','Sexta']
FAIXAS_GRADE = ['19h00 - 21h00','21h00 - 23h00']

GRADE_LETRAS = [
    ['A','C','E','B','D'],  # 19-21
    ['B','D','A','C','E'],  # 21-23
]

# Todos os slots possíveis da grade (combinação dia x faixa)
all_slots = []
for f, faixa in enumerate(FAIXAS_GRADE):
    for j, dia in enumerate(DIAS_GRADE):
        all_slots.append((dia, faixa))
slot_index = {s: i for i, s in enumerate(all_slots)}
n_slots = len(all_slots)

# Disponibilidade real do aluno 
A = np.zeros((n_students, n_slots), dtype=int)
for s_idx, row in df_bct.iterrows():
    for slot in slots_from_json(row['horario']):
        if slot in slot_index:
            A[s_idx, slot_index[slot]] = 1

# Letras e os 2 horários fixos de cada letra
letters = ['A','B','C','D','E']
letter_index = {L: i for i, L in enumerate(letters)}
n_letters = len(letters)

letter_slots = {L: [] for L in letters}
for f, faixa in enumerate(FAIXAS_GRADE):
    for j, dia in enumerate(DIAS_GRADE):
        L = GRADE_LETRAS[f][j]
        slot = (dia, faixa)
        letter_slots[L].append(slot)

# Matriz B (letra x slot)
B = np.zeros((n_letters, n_slots), dtype=int)
for L in letters:
    li = letter_index[L]
    for slot in letter_slots[L]:
        B[li, slot_index[slot]] = 1

# Aluno está 100% disponível para uma letra se estiver livre nos 2 horários daquela letra
avail_letter = np.zeros((n_students, n_letters), dtype=int)
for s in range(n_students):
    for li, L in enumerate(letters):
        ts = [slot_index[slot] for slot in letter_slots[L]]
        if all(A[s, t] == 1 for t in ts):
            avail_letter[s, li] = 1

print('Slots por letra:')
for L in letters:
    print(L, '->', letter_slots[L])

print('Letras em que cada aluno está 100% disponível:',
      [int(avail_letter[s].sum()) for s in range(n_students)])
# -----------------------------
# 7) Modelo CP-SAT com até 2 turmas por disciplina
# -----------------------------
model = cp_model.CpModel()

# Parâmetros
CAP_TURMA = 5               # máx. 5 alunos por turma (≈ 50 reais)
MIN_ALUNOS_POR_TURMA = 3    # mínimo 3 alunos para uma turma existir (≈ 30 reais)
MAX_TURMAS_POR_DISC = 2     # no máximo 2 turmas por disciplina
MAX_DISC_POR_ALUNO = 5      # como no modelo original (limite de disciplinas por aluno)


n_students = len(df_bct)
n_disc = len(disciplinas)

# Variáveis:
# open_disc[c,k]   : turma k da disciplina c está aberta?
# choose[c,k,li]   : turma k da disciplina c usa a letra L?
# x[s,c,k]         : aluno s está matriculado na turma k da disciplina c?
# z[s,c,k,li]      : aluno s, na turma k da disciplina c, associado à letra L?

open_disc = {}
choose = {}
x = {}
z = {}

for c in range(n_disc):
    for k in range(MAX_TURMAS_POR_DISC):
        open_disc[(c, k)] = model.NewBoolVar(f'open_c{c}_t{k}')
        for li in range(n_letters):
            choose[(c, k, li)] = model.NewBoolVar(f'choose_c{c}_t{k}_L{letters[li]}')

for s in range(n_students):
    for c in range(n_disc):
        if W[s, c] > 0:
            for k in range(MAX_TURMAS_POR_DISC):
                x[(s, c, k)] = model.NewBoolVar(f'x_s{s}_c{c}_t{k}')
                for li in range(n_letters):
                    if avail_letter[s, li] == 1:
                        z[(s, c, k, li)] = model.NewBoolVar(
                            f'z_s{s}_c{c}_t{k}_L{letters[li]}'
                        )

# Cada turma aberta escolhe exatamente UMA letra
for c in range(n_disc):
    for k in range(MAX_TURMAS_POR_DISC):
        model.Add(
            sum(choose[(c, k, li)] for li in range(n_letters))
            == open_disc[(c, k)]
        )

# Mesma disciplina não pode ter duas turmas com a mesma letra
# Para cada disciplina c e cada letra li, a soma sobre turmas k de choose[c,k,li] <= 1
for c in range(n_disc):
    for li in range(n_letters):
        model.Add(
            sum(choose[(c, k, li)] for k in range(MAX_TURMAS_POR_DISC))
            <= 1
        )
# Se aluno cursa (s,c,k), precisa ter pelo menos uma letra atribuída
for (s, c, k), xvar in x.items():
    z_vars = [z[(s, c, k, li)] for li in range(n_letters)
              if (s, c, k, li) in z]
    if z_vars:
        model.Add(xvar <= sum(z_vars))
    else:
        model.Add(xvar == 0)

# z só pode ser 1 se x=1 e a turma escolheu a letra
for (s, c, k, li), zvar in z.items():
    model.Add(zvar <= x[(s, c, k)])
    model.Add(zvar <= choose[(c, k, li)])

# Aluno não pode ter duas disciplinas (ou turmas) na mesma letra
for s in range(n_students):
    for li in range(n_letters):
        z_vars = [z[(ss, c, k, lli)]
                  for (ss, c, k, lli) in z.keys()
                  if ss == s and lli == li]
        if z_vars:
            model.Add(sum(z_vars) <= 1)

# Aluno não pode cursar duas turmas da MESMA disciplina
for s in range(n_students):
    for c in range(n_disc):
        xs = [x[(s, c, k)] for k in range(MAX_TURMAS_POR_DISC)
              if (s, c, k) in x]
        if xs:
            model.Add(sum(xs) <= 1)

# Limite de disciplinas (turmas) por aluno
for s in range(n_students):
    xs = [x[(s, c, k)] for (ss, c, k) in x.keys() if ss == s]
    if xs:
        model.Add(sum(xs) <= MAX_DISC_POR_ALUNO)

# Mínimo de alunos por turma aberta (3) e capacidade da turma (5)
for c in range(n_disc):
    for k in range(MAX_TURMAS_POR_DISC):
        xs = [x[(s, c, k)] for s in range(n_students)
              if (s, c, k) in x]
        if xs:
            # mínimo 3 por turma aberta
            model.Add(sum(xs) >= MIN_ALUNOS_POR_TURMA * open_disc[(c, k)])
            # capacidade máxima 5
            model.Add(sum(xs) <= CAP_TURMA * open_disc[(c, k)])
        else:
            model.Add(open_disc[(c, k)] == 0)

# Aluno só pode cursar turma aberta
for (s, c, k), xvar in x.items():
    model.Add(xvar <= open_disc[(c, k)])

# Objetivo: maximizar soma dos pesos W (satisfação)
objective = []
for (s, c, k), xvar in x.items():
    w = int(W[s, c])
    if w > 0:
        objective.append(w * xvar)

model.Maximize(sum(objective))
print('Modelo montado com até 2 turmas por disciplina.')
# -----------------------------
# 8) Resolver o modelo
# -----------------------------
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 120.0
solver.parameters.num_search_workers = 8

status = solver.Solve(model)
print('Status:', solver.StatusName(status))
# -----------------------------
# 9) Construir grade (disciplinas x turma x letra x slots)
# -----------------------------
from math import isnan

if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
    print('Nenhuma solução viável, ajuste parâmetros.')
else:
    rows = []
    for c, nome in enumerate(disciplinas):
        for k in range(MAX_TURMAS_POR_DISC):
            if solver.Value(open_disc[(c, k)]) == 1:
                for li, L in enumerate(letters):
                    if solver.Value(choose[(c, k, li)]) == 1:
                        for slot in letter_slots[L]:
                            dia, faixa = slot
                            rows.append({
                                'disciplina': nome,
                                'turma': k + 1,  
                                'letra': L,
                                'dia': dia,
                                'faixa': faixa
                            })
    grade_df = pd.DataFrame(rows).sort_values(
        ['disciplina', 'turma', 'dia', 'faixa']
    ).reset_index(drop=True)

    print('Grade noturna (cada disciplina com UMA letra por turma, até 2 turmas):')
    print(grade_df)

    # -----------------------------
    # 10) Número de turmas por matéria
    # -----------------------------
    rows_turmas = []

    for c, nome in enumerate(disciplinas):
        # turmas abertas (1 ou 2)
        turmas_abertas = []
        letras_turmas  = []

        for k in range(MAX_TURMAS_POR_DISC):
            if solver.Value(open_disc[(c, k)]) == 1:
                turmas_abertas.append(k+1)

                # descobrir a letra usada pela turma k
                letra_k = None
                for li, L in enumerate(letters):
                    if solver.Value(choose[(c, k, li)]) == 1:
                        letra_k = L
                        break
                letras_turmas.append(letra_k)

        # número de interessados do modelo
        interessados = counter_total[nome]
        projecao_real = interessados * 10

        rows_turmas.append({
            'disciplina': nome,
            'num_turmas': len(turmas_abertas),
            'interessados_modelo': interessados,
            'projecao_real_aprox': projecao_real,
            'letras_turmas': ', '.join(letras_turmas)
        })

    tabela_turmas_df = pd.DataFrame(rows_turmas).sort_values('disciplina')
    print(tabela_turmas_df)
    
    # -----------------------------
    # 11) Satisfação dos alunos
    # -----------------------------
    sat_rows = []
    for s_idx, row in df_bct.iterrows():
        total_peso = int(W[s_idx, :].sum())
        total_atendido = 0
        discs = []
        letras_ = []
        turmas_ = []

        for c, nome in enumerate(disciplinas):
            for k in range(MAX_TURMAS_POR_DISC):
                if (s_idx, c, k) in x and solver.Value(x[(s_idx, c, k)]) == 1:
                    total_atendido += int(W[s_idx, c])
                    discs.append(nome)
                    turma_c = k + 1
                    letra_c = None
                    for li, L in enumerate(letters):
                        if (s_idx, c, k, li) in z and solver.Value(z[(s_idx, c, k, li)]) == 1:
                            letra_c = L
                            break
                    letras_.append(letra_c)
                    turmas_.append(turma_c)

        sat = total_atendido / total_peso if total_peso > 0 else np.nan
        sat_rows.append({
            'email': row.get('email', None),
            'total_peso': total_peso,
            'total_atendido': total_atendido,
            'satisfacao': sat,
            'disciplinas': ', '.join(discs),
            'turmas': ', '.join(str(t) for t in turmas_),
            'letras': ', '.join(str(L) for L in letras_)
        })

    sat_df = pd.DataFrame(sat_rows)
    print('Satisfação média:', sat_df['satisfacao'].dropna().mean())
    print(sat_df.head())

    # ======================================================
    # 12) Salvar todas as tabelas em um único arquivo Excel
    # ======================================================

    output_path = "/Dados de saida/resultados_grade.xlsx"

    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        grade_df.to_excel(writer, sheet_name="Grade", index=False)
        tabela_turmas_df.to_excel(writer, sheet_name="Resumo_Turmas", index=False)
        sat_df.to_excel(writer, sheet_name="Satisfacao", index=False)

    from google.colab import files
    files.download(output_path)

```
