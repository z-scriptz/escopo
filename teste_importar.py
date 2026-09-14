#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""teste_importar.py -- a ponte entre o "sim" e o dado não pode quebrar.

⚠️ A agência manda o export UMA vez. Se o importador engasgar, a resposta vira
"me manda de novo em outro formato" — e o entusiasmo de quem topou tem prazo de
validade curto. Ele tem que aceitar o que vier.

    python3 teste_importar.py
"""
import csv
import sys
import tempfile
from pathlib import Path

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))
from importar import _horas, _achar, ler_tarefas  # noqa: E402

ok = falhou = 0


def checa(desc, cond, extra=""):
    global ok, falhou
    if cond:
        ok += 1
        print(f"   ✅ {desc}")
    else:
        falhou += 1
        print(f"   ❌ {desc}" + (f"\n      {extra}" if extra else ""))


print("\n── ⚠️ CADA FERRAMENTA ESCREVE HORA DE UM JEITO ──")
checa("decimal simples", _horas("12.5") == 12.5)
checa("decimal com vírgula (padrão BR)", _horas("12,5") == 12.5)
checa("formato 12h30", _horas("12h30") == 12.5, str(_horas("12h30")))
checa("dias + horas do Jira (1d = 8h)", _horas("1d 4h") == 12.0, str(_horas("1d 4h")))
checa("só minutos", abs(_horas("45m") - 0.75) < 0.01, str(_horas("45m")))
checa("com espaço e maiúscula", _horas(" 3H ") == 3.0, str(_horas(" 3H ")))

print("\n   ── ⚠️ e o que NÃO entende vira 0, jamais estimativa ──")
# hora chutada vira valor chutado, que vira cobrança chutada no cliente da
# agência. Prefiro a ocorrência aparecer sem valor e com aviso.
for lixo in ("", None, "n/a", "várias", "-", "???"):
    if _horas(lixo) != 0.0:
        checa("entrada ilegível vira 0.0", False, f"{lixo!r} → {_horas(lixo)}")
        break
else:
    checa("entrada ilegível vira 0.0", True)
checa("hora negativa não vira crédito", _horas("-5") == 0.0)

print("\n── ⚠️ RECONHECER A COLUNA, NÃO EXIGIR RENOMEAR ──")
# pedir pra agência renomear coluna é atrito no pior momento possível
checa("Trello: 'Card Name'", _achar(["Card ID", "Card Name"], "titulo") == "Card Name")
checa("Jira: 'Summary'", _achar(["Issue key", "Summary"], "titulo") == "Summary")
checa("português: 'Título'", _achar(["ID", "Título"], "titulo") == "Título")
checa("coluna que CONTÉM o termo", _achar(["Time Spent (h)"], "horas") == "Time Spent (h)")
checa("coluna ausente devolve vazio", _achar(["A", "B"], "horas") == "")

print("\n── o export real, com as sujeiras que ele tem ──")
tmp = Path(tempfile.mkdtemp())
arq = tmp / "export.csv"
arq.write_text("﻿Card ID;Card Name;Description;Tempo\n"
               "T-1;Criar login;Login por email;12h30\n"
               ";;;\n"                       # linha vazia de export
               "T-3;Migrar base;ERP legado;20\n", encoding="utf-8")
tarefas, avisos = ler_tarefas(arq)
checa("⚠️ BOM do Excel não engole a 1ª coluna", len(tarefas) == 2, str(tarefas))
checa("⚠️ ponto-e-vírgula (padrão BR) é detectado", tarefas[0]["id"] == "T-1")
checa("linha vazia não vira tarefa", all(t["titulo"] for t in tarefas))
checa("as horas foram convertidas", tarefas[0]["horas"] == 12.5)

arq2 = tmp / "sem_id.csv"
arq2.write_text("titulo,horas\nFazer coisa,5\nOutra coisa,3\n", encoding="utf-8")
t2, _ = ler_tarefas(arq2)
checa("sem coluna de id, gera T-001…", [x["id"] for x in t2] == ["T-001", "T-002"],
      str([x["id"] for x in t2]))

arq3 = tmp / "sem_horas.csv"
arq3.write_text("titulo\nUma coisa\n", encoding="utf-8")
t3, av3 = ler_tarefas(arq3)
checa("sem coluna de horas, importa mesmo assim", len(t3) == 1)
checa("⚠️ …mas AVISA que o laudo sai sem R$",
      any("HORAS" in a for a in av3), str(av3))

arq4 = tmp / "sem_titulo.csv"
arq4.write_text("coluna_a,coluna_b\n1,2\n", encoding="utf-8")
try:
    ler_tarefas(arq4)
    checa("sem título, recusa", False, "importou sem saber o que é a tarefa")
except SystemExit as e:
    checa("⚠️ sem coluna de título, recusa", True)
    checa("…e mostra as colunas que EXISTEM (senão o erro não ajuda)",
          "coluna_a" in str(e), str(e))

print(f"\n{'='*66}\n   {ok} passou · {falhou} falhou\n{'='*66}")
raise SystemExit(1 if falhou else 0)
