#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""relimiar.py -- e se o LIMIAR_FORA fosse outro? Sem gastar uma chamada.

⚠️ POR QUE ISTO EXISTE.

A pergunta "0.85 ou 0.95?" estava virando discussão de opinião entre três
partes. Mas ela **já tem resposta nos dados que a gente gravou** — cada linha do
log tem a confiança declarada e a classe original.

📌 O log guarda `rebaixada`, então dá pra reconstruir o que o modelo REALMENTE
disse antes do limiar mexer. Sem isso, replay seria impossível e a única saída
seria rodar tudo de novo a cada palpite.

Isso transforma escolha de parâmetro em medição — e deixa o custo em zero, o que
importa porque parâmetro que custa dinheiro pra testar acaba sendo escolhido por
intuição.

    python3 relimiar.py                      # todos os logs
    python3 relimiar.py execucoes/X.jsonl    # um específico
"""
import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))
from escopo.metricas import Metricas, DENTRO, FORA, AMBIGUO  # noqa: E402

LIMIARES = (0.80, 0.85, 0.90, 0.93, 0.95, 0.98)


def carregar(caminhos) -> list:
    linhas = []
    for c in caminhos:
        for ln in Path(c).read_text(encoding="utf-8").splitlines():
            if ln.strip():
                linhas.append(json.loads(ln))
    return linhas


def classe_original(r: dict) -> str:
    """⚠️ O que o modelo disse ANTES do motor rebaixar. É o único jeito de
    replay: sem isto, o log só guarda o efeito do limiar antigo e simular outro
    seria impossível."""
    return FORA if r.get("rebaixada") else r.get("predito", AMBIGUO)


def simular(linhas: list, limiar: float) -> Metricas:
    m = Metricas()
    for r in linhas:
        classe = classe_original(r)
        conf = float(r.get("confianca") or 0)
        if classe == FORA and conf < limiar:
            classe = AMBIGUO
        m.add(r.get("gabarito", "?"), classe, r.get("dificuldade", "?"),
              r.get("tarefa", ""), confianca=conf)
    return m


def main() -> int:
    alvos = sys.argv[1:] or sorted((BASE / "execucoes").glob("*.jsonl"))
    if not alvos:
        print("\n❌ nenhum log em execucoes/ — rode `python3 avaliar.py` antes\n")
        return 1
    linhas = carregar(alvos)
    modelos = sorted({r.get("modelo", "?") for r in linhas})
    prompts = sorted({r.get("prompt_versao", "?") for r in linhas})
    print(f"\n{len(linhas)} tarefa(s) de {len(alvos)} execução(ões)")
    print(f"modelo(s): {', '.join(modelos)} · prompt(s): {', '.join(prompts)}")
    # ⚠️ misturar prompts diferentes num replay só compara coisas incomparáveis
    if len(prompts) > 1:
        print("⚠️ MAIS DE UMA VERSÃO DE PROMPT no mesmo replay — os números "
              "abaixo somam execuções que não são comparáveis entre si.")

    print(f"\n{'limiar':>7} {'🔴 prec':>8} {'falso🔴':>8} {'cobert':>7} "
          f"{'🟡':>6} {'concord':>8}   acusações")
    print("─" * 72)
    for lim in LIMIARES:
        m = simular(linhas, lim)
        n_ac = m._n(pred=FORA)
        certos = m._n(gab=FORA, pred=FORA)
        pv = m.precisao_vermelho
        print(f"{lim:>7.2f} "
              f"{('  —  ' if pv is None else f'{pv:>7.0%}')} "
              f"{('  —  ' if pv is None else f'{1-pv:>7.0%}')} "
              f"{m.cobertura:>6.0%} {m.taxa_amarelo:>5.0%} "
              f"{m.concordancia:>7.0%}   {certos}/{n_ac} procedem")

    # ⚠️ O QUE A TABELA NÃO DIZ, e é o que mais importa na decisão.
    print("\n" + "─" * 72)
    reds = [(float(r.get("confianca") or 0), r.get("gabarito") == FORA,
             r.get("tarefa", ""), r.get("dificuldade", "?"))
            for r in linhas if classe_original(r) == FORA]
    reds.sort(reverse=True)
    print(f"  as {len(reds)} acusações do modelo, por confiança:")
    for conf, certo, tid, dif in reds:
        print(f"     {conf:>5.0%}  {'✅' if certo else '❌ INDEVIDA'}  "
              f"{tid:<8} [{dif}]")
    certos = [c for c, ok, _, _ in reds if ok]
    errados = [c for c, ok, _, _ in reds if not ok]
    if certos and errados:
        print(f"\n  menor confiança entre os CERTOS:   {min(certos):.0%}")
        print(f"  maior confiança entre os ERRADOS:  {max(errados):.0%}")
        if min(certos) > max(errados):
            print(f"  📌 SEPARAÇÃO LIMPA: qualquer limiar entre "
                  f"{max(errados):.0%} e {min(certos):.0%} zera a acusação "
                  f"indevida sem perder nenhum acerto.")
        else:
            print(f"  ⚠️ SEM SEPARAÇÃO LIMPA: existe erro com confiança maior "
                  f"que algum acerto. Limiar nenhum resolve — o problema é do "
                  f"classificador, não do corte.")
    print(f"\n  ⚠️ {len(reds)} acusações é amostra pequena. Separação limpa aqui "
          f"é indício,\n     não prova — e some com um único contraexemplo.\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
