#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""teste_motor.py -- o motor determinístico, sem rede e sem LLM.

⚠️ O QUE ESTE TESTE MEDE E O QUE ELE NÃO MEDE.

Ele mede o MOTOR: limiar, conta, agregação, degradação. O classificador é um
dublê que devolve o que eu mandar — então nada aqui prova que a IA classifica
bem. Isso é o `avaliar.py`, que roda contra o corpus com um modelo de verdade.

📌 Misturar os dois faria a suíte ficar verde por causa do dublê enquanto a
classificação real estivesse péssima — que é a forma mais comum de teste mentir.

    python3 teste_motor.py
"""
import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))
from escopo.motor import (avaliar, relatorio, LIMIAR_FORA,  # noqa: E402
                          DENTRO, FORA, AMBIGUO, _valor)

ok = falhou = 0


def checa(desc, cond, extra=""):
    global ok, falhou
    if cond:
        ok += 1
        print(f"   ✅ {desc}")
    else:
        falhou += 1
        print(f"   ❌ {desc}" + (f"\n      {extra}" if extra else ""))


def dublê(respostas):
    """Classificador falso: devolve o que eu mandar, por id de tarefa."""
    return lambda _txt, t: respostas.get(t.get("id"), {})


CONTRATO = {"cliente": "X", "valor": 40000.0, "valor_hora": 200.0, "texto": "..."}


print("\n── ⚠️ A CONTA É DO CÓDIGO, NUNCA DO MODELO ──")
# se um dia alguém deixar o LLM devolver "valor", ele tem que ser ignorado
_r = avaliar(CONTRATO, [{"id": "A", "titulo": "t", "horas": 10}],
             dublê({"A": {"classificacao": FORA, "confianca": 0.99,
                          "valor": 999999.0}}))
checa("valor = horas × valor_hora", _r.ocorrencias[0].valor == 2000.0,
      str(_r.ocorrencias[0].valor))
checa("⚠️ valor vindo do modelo é IGNORADO", _r.valor_fora == 2000.0,
      "número inventado por LLM entrou numa cobrança")
checa("sem horas, valor é 0 e não uma estimativa",
      _valor(None, 200) == 0.0 and _valor("", 200) == 0.0)
checa("hora negativa não vira crédito", _valor(-5, 200) == 0.0)
checa("hora não-numérica não quebra", _valor("oito", 200) == 0.0)

print("\n── ⚠️⚠️ O LIMIAR É ASSIMÉTRICO (a tese do produto) ──")
# errar pra menos custa dinheiro; errar pra mais custa a confiança da agência
# com o cliente dela — e isso não volta
_r = avaliar(CONTRATO, [{"id": "A", "titulo": "t", "horas": 10}],
             dublê({"A": {"classificacao": FORA, "confianca": 0.60}}))
checa("'fora' com confiança baixa NÃO vira 🔴",
      _r.ocorrencias[0].classificacao == AMBIGUO,
      "acusação fraca chegando no cliente da agência")
checa("…e é marcada como rebaixada (o usuário vê por quê)",
      _r.ocorrencias[0].rebaixada)
checa("…e sai do total de extraescopo", _r.valor_fora == 0.0)
checa("…mas continua contada em revisão", _r.valor_ambiguo == 2000.0)

_r = avaliar(CONTRATO, [{"id": "A", "titulo": "t", "horas": 10}],
             dublê({"A": {"classificacao": FORA, "confianca": 0.95}}))
checa("'fora' com confiança alta vira 🔴 mesmo",
      _r.ocorrencias[0].classificacao == FORA and _r.valor_fora == 2000.0)

_r = avaliar(CONTRATO, [{"id": "A", "titulo": "t", "horas": 10}],
             dublê({"A": {"classificacao": DENTRO, "confianca": 0.20}}))
checa("⚠️ 'dentro' com confiança baixa CONTINUA 🟢 (assimetria)",
      _r.ocorrencias[0].classificacao == DENTRO,
      "rebaixar 'dentro' encheria o laudo de 🟡 sem proteger ninguém")

print("\n── ⚠️ RESPOSTA ESTRANHA DO MODELO NUNCA VIRA ACUSAÇÃO ──")
for lixo in ({"classificacao": "EXTRAESCOPO!!", "confianca": 0.99},
             {"classificacao": None, "confianca": 0.99},
             {"confianca": 0.99},
             {}, None):
    _r = avaliar(CONTRATO, [{"id": "A", "titulo": "t", "horas": 10}],
                 lambda _t, _x, _l=lixo: _l)
    if _r.ocorrencias[0].classificacao == FORA:
        break
else:
    checa("classe desconhecida/ausente cai em 🟡, nunca em 🔴", True)
checa("confiança não-numérica vira 0",
      avaliar(CONTRATO, [{"id": "A", "horas": 1}],
              dublê({"A": {"classificacao": FORA, "confianca": "muito"}})
              ).ocorrencias[0].confianca == 0.0)
checa("confiança acima de 1 é grampeada",
      avaliar(CONTRATO, [{"id": "A", "horas": 1}],
              dublê({"A": {"classificacao": FORA, "confianca": 7}})
              ).ocorrencias[0].confianca == 1.0)

print("\n── ⚠️ 🟡 NUNCA SOMA COM 🔴 ──")
# somar os dois num número só transforma "pode ser" em "é", no lugar exato
# onde a agência decide se leva a cobrança pro cliente
_r = avaliar(CONTRATO,
             [{"id": "A", "titulo": "a", "horas": 10},
              {"id": "B", "titulo": "b", "horas": 20}],
             dublê({"A": {"classificacao": FORA, "confianca": 0.95},
                    "B": {"classificacao": AMBIGUO, "confianca": 0.50}}))
checa("o total 🔴 leva só o que é 🔴", _r.valor_fora == 2000.0)
checa("o 🟡 aparece, separado", _r.valor_ambiguo == 4000.0)
_txt = relatorio(_r)
checa("o relatório mostra os dois em linhas distintas",
      "POTENCIALMENTE FORA" in _txt and "em revisão (não somado acima)" in _txt)
checa("⚠️ e nunca diz que o cliente DEVE",
      "deve" not in _txt.lower().replace("devolve", ""),
      "linguagem de cobrança sobre uma detecção não validada")

print("\n── ⚠️ A COBERTURA É MÉTRICA DE PRIMEIRA CLASSE ──")
# precisão sem cobertura não é produto: se tudo cair em 🟡, a agência recebeu
# uma lista de "sei lá" e faz o trabalho na mão, que é o que ela já fazia
_todas_ambiguas = avaliar(
    CONTRATO, [{"id": str(i), "horas": 1} for i in range(10)],
    lambda _t, _x: {"classificacao": AMBIGUO, "confianca": 0.5})
checa("laudo 100% ambíguo tem cobertura 0", _todas_ambiguas.taxa_decidida == 0.0)
checa("…e o relatório diz isso na cara",
      "cobertura decidida: 0%" in relatorio(_todas_ambiguas))
_metade = avaliar(
    CONTRATO, [{"id": str(i), "horas": 1} for i in range(10)],
    lambda _t, x: {"classificacao": DENTRO if int(x["id"]) < 5 else AMBIGUO,
                   "confianca": 0.9})
checa("cobertura de metade dá 50%", _metade.taxa_decidida == 0.5)
checa("laudo vazio não divide por zero",
      avaliar(CONTRATO, [], dublê({})).taxa_decidida == 0.0)

print("\n── ⚠️ O LAUDO VAI PRO CLIENTE DA AGÊNCIA: formato tem que ser BR ──")
# ⚠️ A 1ª versão imprimia `R$ 42,000.00`. Num documento de cobrança em
# português isso parece ferramenta estrangeira mal traduzida — e a primeira
# coisa que o laudo precisa transmitir é competência.
from escopo.motor import brl, num  # noqa: E402
checa("milhar com ponto, decimal com vírgula", brl(42000) == "R$ 42.000,00", brl(42000))
checa("milhão também", brl(1234567.89) == "R$ 1.234.567,89", brl(1234567.89))
checa("valor pequeno não ganha separador", brl(180) == "R$ 180,00", brl(180))
checa("zero e None não quebram", brl(0) == "R$ 0,00" and brl(None) == "R$ 0,00")
# ⚠️ o `num` nasceu com `.replace(",", ".")` e devolvia "1.234.5" — dois
# separadores iguais, nenhuma vírgula. Passou batido porque os casos de teste
# tinham menos de mil horas.
checa("⚠️ horas acima de mil não saem com dois pontos", num(1234.5) == "1.234,5",
      num(1234.5))
checa("horas abaixo de mil", num(112.0) == "112,0", num(112.0))
checa("o relatório inteiro não tem separador americano",
      not __import__("re").search(r"R\$ [\d.]*\d,\d{3}\b", relatorio(_metade)),
      relatorio(_metade)[:200])

print("\n── a cobertura é fração, não inteiro arredondado ──")
# ⚠️ era `round(len(dentro) + len(fora), 4) / n` — arredondava o INTEIRO (no-op)
# e deixava a divisão solta, devolvendo 0.3333333333333333
_terco = avaliar(CONTRATO, [{"id": str(i), "horas": 1} for i in range(3)],
                 lambda _t, x: {"classificacao": DENTRO if x["id"] == "0" else AMBIGUO,
                                "confianca": 0.9})
checa("1 de 3 decididas vira 0.3333", _terco.taxa_decidida == 0.3333,
      str(_terco.taxa_decidida))

print("\n── os casos sintéticos carregam o gabarito humano ──")
casos = sorted((BASE / "casos").glob("*.json"))
checa("existe pelo menos um caso", len(casos) >= 1)
for arq in casos:
    d = json.loads(arq.read_text(encoding="utf-8"))
    esperados = [t.get("esperado") for t in d["tarefas"]]
    checa(f"{arq.name}: todo gabarito é válido",
          all(e in (DENTRO, FORA, AMBIGUO) for e in esperados),
          str(set(esperados)))
    checa(f"{arq.name}: todo caso explica o PORQUÊ",
          all((t.get("porque") or "").strip() for t in d["tarefas"]),
          "gabarito sem motivo é opinião, não referência")
    # ⚠️ um corpus só de casos fáceis dá 100% e não ensina nada
    checa(f"{arq.name}: tem caso ambíguo (senão o corpus é fácil demais)",
          AMBIGUO in esperados, str(esperados))
    # o motor tem que atravessar o caso real sem estourar
    _l = avaliar(d["contrato"], d["tarefas"],
                 lambda _t, t: {"classificacao": t.get("esperado"),
                                "confianca": 0.95})
    checa(f"{arq.name}: motor atravessa o caso inteiro",
          len(_l.ocorrencias) == len(d["tarefas"]))
    checa(f"{arq.name}: relatório gera sem quebrar", bool(relatorio(_l)))

print(f"\n{'='*66}\n   {ok} passou · {falhou} falhou\n{'='*66}")
raise SystemExit(1 if falhou else 0)
