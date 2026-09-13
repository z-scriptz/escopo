#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""avaliar.py -- roda o corpus contra um modelo real e MEDE.

⚠️ ESTE ARQUIVO PODE SER MAIS IMPORTANTE QUE O CLASSIFICADOR.

Sem ele, trocar prompt ou modelo é respondido com *"parece melhor"*. Com ele é
respondido com precisão, cobertura e a lista de erros. É o que permite comparar
Gemini caro × Gemini barato × Claude × GPT sobre o MESMO gabarito e escolher com
número em vez de impressão.

⚠️⚠️ E O QUE ELE **NÃO** PROVA:

O corpus é sintético — eu escrevi os contratos E o gabarito. Então uma nota boa
aqui significa *"o modelo concorda com quem escreveu o corpus"*, não *"o modelo
acerta"*. Serve pra pegar falha grosseira e pra detectar regressão ao trocar de
modelo. **Validação de produto só vem de contrato real com a classificação da
própria agência.** Não confunda os dois — a diferença é o projeto inteiro.

    python3 avaliar.py                    # usa CLASSIFIER_MODEL do .env
    python3 avaliar.py --provedor dublê   # sem chave, só pra ver o encanamento
    python3 avaliar.py --modelos          # lista o que a conta pode chamar
"""
import argparse
import json
import os
import sys
import time
from pathlib import Path

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))

from escopo import classificador as C          # noqa: E402
from escopo import provedor as P               # noqa: E402
from escopo.metricas import Metricas, relatorio as rel_metricas  # noqa: E402
from escopo.motor import avaliar as motor_avaliar, relatorio as rel_laudo  # noqa: E402

EXECUCOES = BASE / "execucoes"


def carregar_env(base: Path = BASE) -> int:
    """⚠️ Nunca sobrescreve variável já exportada, e vazia conta como ausente.
    (Lição herdada do projeto anterior: 40 cópias dessa função, nenhuma igual.)"""
    arq = base / ".env"
    n = 0
    try:
        for linha in arq.read_text(encoding="utf-8").splitlines():
            linha = linha.strip()
            if not linha or linha.startswith("#") or "=" not in linha:
                continue
            if linha.lower().startswith("export "):
                linha = linha[7:]
            k, _, v = linha.partition("=")
            k, v = k.strip(), v.strip().strip('"').strip("'")
            if k and not os.environ.get(k):
                os.environ[k] = v
                n += 1
    except Exception:
        pass
    return n


def casos(so=None) -> list:
    saida = []
    for arq in sorted((BASE / "casos").glob("*.json")):
        d = json.loads(arq.read_text(encoding="utf-8"))
        if not so or so in d["id"]:
            saida.append(d)
    return saida


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--provedor", default="")
    ap.add_argument("--modelo", default="")
    ap.add_argument("--caso", default="", help="roda só os casos com este texto no id")
    ap.add_argument("--modelos", action="store_true",
                    help="lista os modelos que ESTA conta pode chamar e sai")
    ap.add_argument("--laudo", action="store_true", help="imprime o laudo de cada caso")
    a = ap.parse_args()

    carregar_env()
    if a.modelo:
        os.environ["CLASSIFIER_MODEL"] = a.modelo

    try:
        prov = P.criar(a.provedor)
    except P.ErroProvedor as e:
        print(f"\n❌ {e}\n")
        return 1

    if a.modelos:
        # ⚠️ QUEM DIZ QUE O MODELO EXISTE É A API, NÃO A MINHA LEMBRANÇA.
        ms = prov.modelos()
        print(f"\n{len(ms)} modelo(s) chamáveis nesta conta:\n")
        for m in ms:
            print(f"   {'→' if m == getattr(prov, 'modelo', '') else ' '} {m}")
        print()
        return 0

    # falha cedo, com a lista na mão: descobrir o ID errado na chamada 200
    # é perder a rodada inteira
    try:
        prov.validar_modelo()
    except P.ErroProvedor as e:
        print(f"\n❌ {e}\n")
        return 1

    classificar = C.classificar_com(prov)
    m = Metricas()
    EXECUCOES.mkdir(exist_ok=True)
    carimbo = time.strftime("%Y%m%d_%H%M%S")
    log = EXECUCOES / f"{carimbo}_{prov.nome}.jsonl"
    tok_in = tok_out = 0
    t0 = time.time()

    print(f"\nprovedor {prov.nome} · modelo {getattr(prov, 'modelo', '?')} · "
          f"prompt {C.PROMPT_VERSAO}")

    for d in casos(a.caso):
        print(f"\n── {d['id']} ──")
        gab = {t["id"]: t for t in d["tarefas"]}
        laudo = motor_avaliar(d["contrato"], d["tarefas"], classificar)
        for o in laudo.ocorrencias:
            t = gab.get(o.id, {})
            esperado = t.get("esperado", "?")
            r = classificar.ultima
            acertou = (esperado == o.classificacao)
            m.add(esperado, o.classificacao, t.get("dificuldade", "?"), o.id,
                  confianca=o.confianca)
            if r:
                tok_in += r.tokens_entrada
                tok_out += r.tokens_saida
            # ⚠️ UMA LINHA POR TAREFA, com TUDO. É o que permite comparar
            # execuções velhas com novas sem depender de memória.
            with open(log, "a", encoding="utf-8") as f:
                f.write(json.dumps({
                    "caso": d["id"], "tarefa": o.id,
                    "modelo": getattr(r, "modelo", ""),
                    "prompt_versao": C.PROMPT_VERSAO,
                    "gabarito": esperado, "predito": o.classificacao,
                    "rebaixada": o.rebaixada,
                    "confianca": o.confianca,
                    "dificuldade": t.get("dificuldade", "?"),
                    "acertou": acertou,
                    "clausula": o.clausula, "justificativa": o.justificativa,
                    "tokens_entrada": getattr(r, "tokens_entrada", 0),
                    "tokens_saida": getattr(r, "tokens_saida", 0),
                    "duracao": getattr(r, "duracao", 0),
                }, ensure_ascii=False) + "\n")
            marca = "✅" if acertou else "❌"
            print(f"   {marca} {o.id:<6} [{t.get('dificuldade','?'):<9}] "
                  f"gabarito={esperado:<8} nós={o.classificacao:<8} "
                  f"({o.confianca:.0%})")
        if a.laudo:
            print("\n" + rel_laudo(laudo))

    print()
    print(rel_metricas(m))
    dt = time.time() - t0
    n = max(1, m.total)
    print(f"  {tok_in:,} tokens entrada · {tok_out:,} tokens saída · "
          f"{tok_in / n:,.0f} entrada/tarefa")
    print(f"  {dt:.1f}s no total · {dt / n:.2f}s por tarefa")
    print(f"  log: {log.relative_to(BASE)}")
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
