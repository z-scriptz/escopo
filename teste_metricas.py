#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""teste_metricas.py -- a régua tem que estar certa antes de medir qualquer coisa.

⚠️ POR QUE ISTO EXISTE ANTES DE QUALQUER MEDIÇÃO REAL.

Toda decisão de modelo, prompt e estratégia vai sair destes números. Régua
errada não dá erro: dá um número plausível, e a gente segue a direção errada com
confiança. Já vi isso esta semana num relatório que dizia "36 fontes MORTAS"
porque a consulta de vendas tinha falhado e o vazio virou zero.

    python3 teste_metricas.py
"""
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))
from escopo.metricas import Metricas, relatorio  # noqa: E402
from escopo import provedor as P                 # noqa: E402

DENTRO, FORA, AMBIGUO = "dentro", "fora", "ambiguo"
ok = falhou = 0


def checa(desc, cond, extra=""):
    global ok, falhou
    if cond:
        ok += 1
        print(f"   ✅ {desc}")
    else:
        falhou += 1
        print(f"   ❌ {desc}" + (f"\n      {extra}" if extra else ""))


def m_de(pares, dif="easy"):
    m = Metricas()
    for i, (g, p) in enumerate(pares):
        m.add(g, p, dif, f"T-{i:02d}")
    return m


print("\n── ⚠️⚠️ A MÉTRICA SAGRADA: acusação indevida ──")
# o pior dia do ESCOPO não é deixar R$2.000 passar. É a agência dizer "R$8.000
# fora do escopo" e o cliente responder "está na página 4 do contrato".
m = m_de([(FORA, FORA), (FORA, FORA), (FORA, FORA), (DENTRO, FORA)])
checa("precisão 🔴 = 3 de 4", m.precisao_vermelho == 0.75, str(m.precisao_vermelho))
checa("falso vermelho = 25%", m.falso_vermelho == 0.25)
checa("⚠️ ele conta o AMBÍGUO virando 🔴 também",
      m_de([(AMBIGUO, FORA), (FORA, FORA)]).falso_vermelho == 0.5,
      "acusar o que era pra ser revisado é acusação indevida do mesmo jeito")

print("\n── ⚠️ NÃO ACUSAR NINGUÉM NÃO É ACERTAR ──")
# um motor que responde 🟡 pra tudo teria precisão 100% se isso virasse 1.0 —
# e ele é exatamente o motor inútil que a cobertura existe pra pegar
m = m_de([(FORA, AMBIGUO), (FORA, AMBIGUO)])
checa("precisão 🔴 sem nenhum 🔴 é None, não 1.0", m.precisao_vermelho is None)
checa("…e o relatório mostra '—', não '100%'", " —  " in relatorio(m))
checa("…e a cobertura denuncia: 0%", m.cobertura == 0.0)

print("\n── ⚠️ OS DOIS ERROS NÃO SÃO SIMÉTRICOS ──")
m = m_de([(FORA, DENTRO), (FORA, DENTRO), (FORA, FORA), (FORA, FORA)])
checa("dinheiro perdido = 2 de 4 que eram 🔴", m.dinheiro_perdido == 0.5)
checa("…e isso NÃO conta como falso vermelho",
      m.falso_vermelho == 0.0,
      "deixar passar e acusar errado são erros de custo diferente")

print("\n── cobertura e taxa amarela ──")
m = m_de([(DENTRO, DENTRO), (FORA, FORA), (FORA, AMBIGUO), (DENTRO, AMBIGUO)])
checa("cobertura = metade", m.cobertura == 0.5)
checa("taxa 🟡 = metade", m.taxa_amarelo == 0.5)
checa("cobertura + taxa 🟡 = 1", m.cobertura + m.taxa_amarelo == 1.0)
checa("sem linhas, não divide por zero",
      Metricas().cobertura == 0.0 and Metricas().concordancia == 0.0)

print("\n── ⚠️ AVISO DE AMOSTRA PEQUENA VEM ANTES DOS NÚMEROS ──")
# precisão medida em 6 casos muda 17 pontos com um erro. Número com cara de
# ciência e tamanho de anedota é pior que número nenhum.
_txt = relatorio(m_de([(FORA, FORA)] * 5))
checa("corpus pequeno é marcado como tal", "AMOSTRA PEQUENA" in _txt)
checa("…e diz quanto UM erro move a precisão", "pontos" in _txt)
checa("…e o aviso vem antes da primeira métrica",
      _txt.index("AMOSTRA PEQUENA") < _txt.index("precisão"))
checa("corpus grande não leva o aviso",
      "AMOSTRA PEQUENA" not in relatorio(m_de([(FORA, FORA)] * 40)))

print("\n── ⚠️ POR DIFICULDADE: é o que revela corpus fácil demais ──")
m = Metricas()
for i in range(8):
    m.add(FORA, FORA, "easy", f"E{i}")        # acerta tudo no fácil
for i in range(4):
    m.add(DENTRO, FORA, "trap", f"X{i}")      # erra tudo na armadilha
checa("o fácil aparece em 100%", m.por_dificuldade()["easy"]["taxa"] == 1.0)
checa("⚠️ e a armadilha em 0% — a média sozinha esconderia isso",
      m.por_dificuldade()["trap"]["taxa"] == 0.0,
      f"concordância geral seria {m.concordancia:.0%} e pareceria aceitável")
checa("a concordância geral de fato disfarça", m.concordancia == 8 / 12)

print("\n── ⚠️ OS ERROS SAEM EM ORDEM DE GRAVIDADE ──")
m = Metricas()
m.add(FORA, DENTRO, "medium", "PERDIDO")      # dinheiro perdido
m.add(DENTRO, FORA, "trap", "ACUSADO")        # acusação indevida
m.add(FORA, AMBIGUO, "hard", "DUVIDA")        # divergência leve
_erros = m.erros()
checa("acusação indevida vem primeiro", _erros[0][3] == "ACUSADO", str(_erros))
checa("dinheiro perdido vem depois", _erros[1][3] == "PERDIDO")
checa("o relatório rotula a acusação indevida",
      "ACUSAÇÃO INDEVIDA" in relatorio(m))

print("\n── ⚠️ PRECISÃO 🔴 E FPR RESPONDEM PERGUNTAS DIFERENTES ──")
# ⚠️ com classes desbalanceadas uma esconde a outra. Projeto com 2 extraescopos
# em 200 tarefas: acusar 2 certas e 2 erradas dá precisão 50% e FPR de 1%.
m = Metricas()
m.add(FORA, FORA, "easy", "A");  m.add(FORA, FORA, "easy", "B")
m.add(DENTRO, FORA, "trap", "C"); m.add(DENTRO, FORA, "trap", "D")
for i in range(196):
    m.add(DENTRO, DENTRO, "easy", f"Z{i}")
checa("precisão 🔴 = 2 de 4 acusados", m.precisao_vermelho == 0.5)
checa("⚠️ mas a FPR é ~1% (2 erradas em 198 que estavam dentro)",
      abs(m.taxa_falso_positivo - 2 / 198) < 1e-9,
      str(m.taxa_falso_positivo))
checa("as duas aparecem no relatório",
      "precisão (dos que acusamos" in relatorio(m)
      and "FP/(FP+TN)" in relatorio(m))
checa("sem nenhum caso 'dentro', FPR é None em vez de dividir por zero",
      m_de([(FORA, FORA)]).taxa_falso_positivo is None)

print("\n── ⚠️ CONFIANÇA É SCORE DECLARADO, NÃO PROBABILIDADE ──")
# "0,93" não quer dizer 93% de chance de acerto. LLM costuma ser mal calibrado,
# e o LIMIAR_FORA=0.85 de hoje é palpite — esta tabela é o que um dia troca o
# palpite por medição.
m = Metricas()
for _ in range(10):
    m.add(FORA, FORA, "easy", "x", confianca=0.97)      # alta e certa
for _ in range(10):
    m.add(DENTRO, FORA, "trap", "y", confianca=0.92)    # alta e ERRADA
cal = m.calibracao()
checa("a faixa 0.95+ aparece com acerto alto", cal["0.95–1.00"]["acerto"] == 1.0)
checa("⚠️ e a faixa 0.90–0.95 denuncia score alto com acerto zero",
      cal["0.90–0.95"]["acerto"] == 0.0, str(cal))
checa("o relatório avisa que score não é probabilidade",
      "NÃO probabilidade" in relatorio(m))
checa("sem confiança registrada, a tabela some em vez de mentir",
      m_de([(FORA, FORA)]).calibracao() == {})

print("\n── o provedor não deixa ID de modelo inventado passar ──")
# ⚠️ eu não tenho como verificar, escrevendo isto, que um dado ID existe.
# Quem responde é a API — e ela responde ANTES da avaliação, não no meio.
d = P.Dublê(modelo="modelo-real-1",
            disponiveis=["modelo-real-1", "gemini-flash-x", "gemini-pro-x"])
checa("modelo que existe passa", d.validar_modelo() == "modelo-real-1")
d.modelo = "gemini-inventado-9.9-flash"
try:
    d.validar_modelo()
    checa("⚠️ modelo inexistente é recusado", False, "passou batido")
except P.ErroProvedor as e:
    checa("⚠️ modelo inexistente é recusado ANTES de gastar chamada", True)
    checa("…e o erro mostra o que existe de verdade", "Parecidos" in str(e))
try:
    P.criar("provedor-que-nao-existe")
    checa("provedor desconhecido é recusado", False, "aceitou qualquer nome")
except P.ErroProvedor as e:
    checa("provedor desconhecido é recusado", True)
    checa("…e o erro lista os que existem", "gemini" in str(e), str(e))


def _sem_chave():
    import os
    antes = os.environ.pop("GEMINI_API_KEY", None)
    try:
        P.Gemini(modelo="x")
        return ""
    except P.ErroProvedor as e:
        return str(e)
    finally:
        if antes:
            os.environ["GEMINI_API_KEY"] = antes


_msg = _sem_chave()
checa("⚠️ sem chave, falha dizendo onde ela deve morar", "env" in _msg.lower(),
      _msg)
checa("…e a mensagem manda NÃO colar no chat", "chat" in _msg.lower(), _msg)

print(f"\n{'='*66}\n   {ok} passou · {falhou} falhou\n{'='*66}")
raise SystemExit(1 if falhou else 0)
