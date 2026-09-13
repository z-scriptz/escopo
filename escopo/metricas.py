#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""metricas.py -- comparar classificação com gabarito, sem eufemismo.

⚠️ POR QUE ISTO É TÃO IMPORTANTE QUANTO O CLASSIFICADOR.

Daqui a dois meses vamos trocar modelo, prompt e estratégia. Sem isto aqui, a
única resposta possível pra "melhorou?" é *"acho que sim"* — e foi exatamente
assim que o projeto anterior passou 150 dias sem saber o que funcionava.

📌 A MÉTRICA SAGRADA NÃO É ACURÁCIA. É quanto do que mostramos em 🔴 estava
errado. O pior dia do ESCOPO não é deixar R$2.000 passar: é a agência levar
"R$8.000 fora do escopo" pro cliente e ouvir *"está na página 4 do contrato"*.
Depois disso ela não abre a ferramenta de novo.
"""
from collections import Counter

DENTRO, FORA, AMBIGUO = "dentro", "fora", "ambiguo"


class Metricas:
    """⚠️ Os dois erros NÃO são simétricos, e por isso têm nomes separados.

    `falso_vermelho`  gabarito diz dentro/ambíguo, nós dissemos 🔴
                      → acusação indevida. Custa a CONFIANÇA. Não volta.
    `dinheiro_perdido` gabarito diz fora, nós dissemos 🟢
                      → deixamos passar. Custa dinheiro que a agência já
                        perdia de qualquer jeito.

    Somar os dois numa "acurácia" esconderia justamente a diferença que
    organiza o produto inteiro.
    """

    def __init__(self):
        self.linhas = []          # (gabarito, predito, dificuldade, id)
        self.confiancas = []      # (confianca, acertou) — para calibração

    def add(self, gabarito, predito, dificuldade="", ident="", confianca=None):
        self.linhas.append((gabarito, predito, dificuldade or "?", ident))
        if confianca is not None:
            self.confiancas.append((float(confianca), gabarito == predito))

    # ── contagens cruas ──
    def _n(self, gab=None, pred=None, dif=None):
        return sum(1 for g, p, d, _ in self.linhas
                   if (gab is None or g == gab)
                   and (pred is None or p == pred)
                   and (dif is None or d == dif))

    @property
    def total(self):
        return len(self.linhas)

    # ── o que decide se o produto serve ──
    @property
    def precisao_vermelho(self):
        """Dos 🔴 que mostramos, quantos o humano confirma."""
        mostrados = self._n(pred=FORA)
        if not mostrados:
            return None            # ⚠️ None, não 1.0: não mostrar nada não é acertar
        return self._n(gab=FORA, pred=FORA) / mostrados

    @property
    def falso_vermelho(self):
        """⚠️ A MÉTRICA SAGRADA. Fração dos 🔴 mostrados que estava errada."""
        p = self.precisao_vermelho
        return None if p is None else 1.0 - p

    @property
    def taxa_falso_positivo(self):
        """FP / (FP + TN) — ⚠️ PERGUNTA DIFERENTE da precisão 🔴.

        precisão 🔴  : dos que ACUSAMOS, quantos procediam
        FPR          : de tudo que estava DENTRO/ambíguo, quanto acusamos à toa

        As duas podem divergir feio quando as classes são desbalanceadas: num
        projeto com 2 extraescopos em 200 tarefas, acusar 2 certas e 2 erradas
        dá precisão 50% e FPR de só 1%. A agência sente a precisão; a saúde do
        classificador aparece na FPR. Sem as duas, uma esconde a outra.
        """
        negativos = self.total - self._n(gab=FORA)     # gabarito != fora
        if not negativos:
            return None
        fp = self._n(pred=FORA) - self._n(gab=FORA, pred=FORA)
        return fp / negativos

    @property
    def precisao_verde(self):
        mostrados = self._n(pred=DENTRO)
        if not mostrados:
            return None
        return self._n(gab=DENTRO, pred=DENTRO) / mostrados

    @property
    def dinheiro_perdido(self):
        """Gabarito 'fora', nós dissemos 'dentro'. Silencioso e caro-pra-ninguém."""
        reais = self._n(gab=FORA)
        if not reais:
            return None
        return self._n(gab=FORA, pred=DENTRO) / reais

    @property
    def cobertura(self):
        """⚠️ Sem ela, precisão não quer dizer nada: um motor que responde 🟡
        pra tudo tem precisão perfeita e utilidade zero."""
        if not self.total:
            return 0.0
        return (self.total - self._n(pred=AMBIGUO)) / self.total

    @property
    def taxa_amarelo(self):
        return 0.0 if not self.total else self._n(pred=AMBIGUO) / self.total

    @property
    def concordancia(self):
        """Acurácia simples. Fica por último de propósito — é a métrica que
        mais engana quando as classes são desbalanceadas."""
        if not self.total:
            return 0.0
        return sum(1 for g, p, _, _ in self.linhas if g == p) / self.total

    # ── por dificuldade: é aqui que dá pra ver se o corpus é fácil demais ──
    def por_dificuldade(self):
        saida = {}
        for dif in sorted({d for _, _, d, _ in self.linhas}):
            n = self._n(dif=dif)
            certos = sum(1 for g, p, d, _ in self.linhas if d == dif and g == p)
            saida[dif] = {"n": n, "acertos": certos, "taxa": certos / n if n else 0.0}
        return saida

    def calibracao(self, faixas=((0.95, 1.01), (0.90, 0.95), (0.85, 0.90),
                                (0.70, 0.85), (0.0, 0.70))):
        """⚠️ "confiança 0,93" NÃO QUER DIZER 93% DE CHANCE DE ACERTO.

        É um score DECLARADO pelo modelo, e LLM costuma ser mal calibrado. Só
        medindo dá pra saber se 0,93 vale 93%, 76% ou 99% — e é essa tabela que
        um dia escolhe o LIMIAR_FORA empiricamente, em vez de por intuição
        (hoje 0.85 é palpite, e está anotado como palpite).
        """
        saida = {}
        for lo, hi in faixas:
            itens = [a for c, a in self.confiancas if lo <= c < hi]
            if itens:
                saida[f"{lo:.2f}–{min(hi, 1.0):.2f}"] = {
                    "n": len(itens),
                    "acerto": sum(itens) / len(itens)}
        return saida

    def erros(self):
        """⚠️ Os erros ensinam mais que os acertos — devolvidos em ordem de
        gravidade: acusação indevida primeiro."""
        def grav(linha):
            g, p, _, _ = linha
            if p == FORA and g != FORA:
                return 0                      # acusação indevida
            if g == FORA and p == DENTRO:
                return 1                      # dinheiro perdido em silêncio
            return 2
        return sorted([l for l in self.linhas if l[0] != l[1]], key=grav)

    def matriz(self):
        return Counter((g, p) for g, p, _, _ in self.linhas)


def _pc(v):
    return "  —  " if v is None else f"{v:>5.0%}"


def relatorio(m: Metricas, minimo_amostra: int = 30) -> str:
    L = []
    L.append("═" * 68)
    L.append(f"  {m.total} tarefa(s) avaliada(s)")
    L.append("═" * 68)
    # ⚠️ O AVISO VEM ANTES DOS NÚMEROS, não num rodapé que ninguém lê.
    # Precisão medida em 6 amostras muda 17 pontos com um erro. Número com
    # cara de ciência e tamanho de anedota é pior que número nenhum.
    n_verm = m._n(pred=FORA)
    if m.total < minimo_amostra:
        L.append(f"  ⚠️ AMOSTRA PEQUENA ({m.total} < {minimo_amostra}). "
                 f"Um erro move a precisão em {100.0/max(1,n_verm):.0f} pontos.")
        L.append(f"     Trate como sinal de falha grosseira, NUNCA como medição.")
        L.append("─" * 68)
    L.append(f"  🔴 precisão (dos que acusamos, quantos procedem)  {_pc(m.precisao_vermelho)}")
    L.append(f"  ⚠️  FALSO VERMELHO  (acusação indevida)           {_pc(m.falso_vermelho)}")
    L.append(f"     taxa de falso positivo  FP/(FP+TN)             {_pc(m.taxa_falso_positivo)}")
    L.append(f"  🟢 precisão                                       {_pc(m.precisao_verde)}")
    L.append(f"     dinheiro perdido (era 🔴, dissemos 🟢)         {_pc(m.dinheiro_perdido)}")
    L.append("─" * 68)
    L.append(f"     cobertura decidida (🟢+🔴)                     {_pc(m.cobertura)}")
    L.append(f"     taxa 🟡                                        {_pc(m.taxa_amarelo)}")
    L.append(f"     concordância geral                             {_pc(m.concordancia)}")
    L.append("─" * 68)
    L.append("  por dificuldade (o produto vive em trap/hard/ambiguous):")
    for dif, d in m.por_dificuldade().items():
        L.append(f"     {dif:<11} {d['acertos']:>2}/{d['n']:<2}  {d['taxa']:>5.0%}")
    cal = m.calibracao()
    if cal:
        L.append("─" * 68)
        L.append("  confiança declarada × acerto real:")
        L.append("  ⚠️ score do modelo, NÃO probabilidade — 0,93 não quer dizer 93%")
        for faixa, d in cal.items():
            L.append(f"     {faixa}   n={d['n']:<3} acertou {d['acerto']:>5.0%}")
    errs = m.erros()
    if errs:
        L.append("─" * 68)
        L.append(f"  ⚠️ {len(errs)} ERRO(S), mais grave primeiro:")
        for g, p, d, i in errs:
            tag = ("ACUSAÇÃO INDEVIDA" if p == FORA and g != FORA else
                   "dinheiro perdido" if g == FORA and p == DENTRO else "divergência")
            L.append(f"     {i:<8} [{d:<9}] gabarito={g:<8} nós={p:<8} {tag}")
    L.append("═" * 68)
    return "\n".join(L)
