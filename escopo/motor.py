#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""motor.py -- a parte determinística. NENHUM número sai de LLM.

⚠️ A REGRA QUE ORGANIZA O ARQUIVO INTEIRO:

    A IA interpreta documento. O código faz conta.

O modelo lê o contrato e diz "esta tarefa parece fora do objeto, cláusula 2,
confiança 0.91". Ele NUNCA diz quanto isso vale. Quem multiplica hora por
valor-hora, soma, aplica limiar e decide o que vira 🔴 é este arquivo — porque
um número inventado por LLM dentro de uma cobrança para o cliente da agência é
o tipo de erro que acaba com o produto no primeiro uso.
"""
import os
from dataclasses import dataclass, field, asdict

# ── ⚠️ O LIMIAR É ASSIMÉTRICO, E ISSO É A TESE DO PRODUTO ─────────────────
# Errar para MENOS custa dinheiro que a agência já perdia mesmo: a tarefa some
# no meio das outras e ninguém cobra. Errar para MAIS custa a CONFIANÇA — a
# agência leva pro cliente uma cobrança de R$3.000 que estava no contrato, o
# cliente mostra a cláusula, e a agência nunca mais abre a ferramenta.
#
# 📌 Então "fora" precisa de evidência forte; "dentro" não precisa de nada.
# Um 🔴 fraco vira 🟡. Um 🟢 fraco continua 🟢 — no máximo a gente deixa
# dinheiro na mesa, que é o estado atual do cliente de qualquer jeito.
LIMIAR_FORA = 0.85

# ── ⚠️ RISCO ECONÔMICO É UM SEGUNDO SINAL, NÃO UM MODIFICADOR DO PRIMEIRO ──
# As horas ficam FORA do prompt de propósito: saber que a tarefa levou 90h
# enviesa o modelo a achar que é grande e portanto extraescopo. São perguntas
# diferentes:
#
#     contratual   "isso estava no contrato?"        → evidência documental
#     econômica    "isso é desproporcional?"          → horas e valor
#
# Contrato de app Android completo + 150h de sincronização offline: grande e
# provavelmente DENTRO. Contrato de ajustar cor de botão + 15 minutos de coisa
# nenhuma a ver: minúsculo e FORA. Tamanho não decide escopo.
#
# 📌 Mas esforço desproporcional é informação valiosa e some se ninguém contar.
# Então ele vira uma COLUNA SEPARADA: "🟡 contratualmente ambíguo · 🔴 risco
# econômico alto · revisão humana recomendada" diz muito mais que qualquer um
# dos dois sozinho — e sem contaminar a classificação contratual.
RISCO_MEDIO = float(os.environ.get("ESCOPO_RISCO_MEDIO", "0.05"))   # 5% do contrato
RISCO_ALTO = float(os.environ.get("ESCOPO_RISCO_ALTO", "0.10"))     # 10% do contrato

# abaixo disto nem como 🟡 vale mostrar: vira ruído e faz o usuário parar de ler
LIMIAR_MOSTRAR = 0.40

DENTRO, FORA, AMBIGUO = "dentro", "fora", "ambiguo"


@dataclass
class Ocorrencia:
    id: str
    titulo: str
    horas: float
    classificacao: str          # dentro | fora | ambiguo
    confianca: float
    clausula: str = ""          # o trecho do contrato que sustenta
    justificativa: str = ""
    valor: float = 0.0          # calculado AQUI, nunca pelo modelo
    rebaixada: bool = False     # era 'fora', virou 'ambiguo' pelo limiar
    risco: str = ""             # "" | medio | alto — sinal SEPARADO da classe

    @property
    def cor(self) -> str:
        return {DENTRO: "🟢", FORA: "🔴", AMBIGUO: "🟡"}.get(self.classificacao, "⬜")


@dataclass
class Laudo:
    projeto: str = ""
    valor_contrato: float = 0.0
    valor_hora: float = 0.0
    ocorrencias: list = field(default_factory=list)

    # ── os números do topo do relatório ──
    @property
    def fora(self) -> list:
        return [o for o in self.ocorrencias if o.classificacao == FORA]

    @property
    def ambiguas(self) -> list:
        return [o for o in self.ocorrencias if o.classificacao == AMBIGUO]

    @property
    def dentro(self) -> list:
        return [o for o in self.ocorrencias if o.classificacao == DENTRO]

    @property
    def valor_fora(self) -> float:
        return round(sum(o.valor for o in self.fora), 2)

    @property
    def riscos(self) -> list:
        """Tarefas grandes demais pro projeto, INDEPENDENTE da classificação."""
        return [o for o in self.ocorrencias if o.risco]

    @property
    def valor_ambiguo(self) -> float:
        """⚠️ SEPARADO do valor_fora, sempre. Somar os dois num número só
        transformaria "pode ser" em "é" no lugar exato onde o usuário decide se
        cobra o cliente dele."""
        return round(sum(o.valor for o in self.ambiguas), 2)

    @property
    def horas_totais(self) -> float:
        return round(sum(o.horas for o in self.ocorrencias), 2)

    @property
    def taxa_decidida(self) -> float:
        """⚠️ A MÉTRICA QUE DIZ SE O PRODUTO EXISTE.

        Fração das tarefas que o motor conseguiu colocar em 🟢 ou 🔴 com
        confiança. Se quase tudo cair em 🟡, o cliente recebeu uma lista de
        "sei lá" e fez o trabalho sozinho — que é o que ele já fazia de graça.
        Precisão sem cobertura não é produto."""
        if not self.ocorrencias:
            return 0.0
        return round((len(self.dentro) + len(self.fora)) / len(self.ocorrencias), 4)


def _valor(horas: float, valor_hora: float) -> float:
    """Conta, e só conta. Hora ausente ou negativa vale zero — nunca estimada.

    ⚠️ Chutar hora aqui seria inventar dinheiro. Quando a agência não apontou
    horas, o certo é a ocorrência aparecer SEM valor e com aviso, pra alguém
    preencher — e não o sistema arbitrar uma média que vira cobrança."""
    try:
        h = float(horas or 0)
    except (TypeError, ValueError):
        return 0.0
    return round(max(0.0, h) * max(0.0, float(valor_hora or 0)), 2)


def avaliar(contrato: dict, tarefas: list, classificar) -> Laudo:
    """Roda o classificador em cada tarefa e aplica as regras determinísticas.

    `classificar(contrato_texto, tarefa) -> dict` é injetado: em teste é um
    dublê, em produção é o LLM. O motor não sabe (nem deve saber) qual é.
    """
    vh = float(contrato.get("valor_hora") or 0)
    laudo = Laudo(projeto=contrato.get("cliente", ""),
                  valor_contrato=float(contrato.get("valor") or 0),
                  valor_hora=vh)

    for t in tarefas or []:
        r = classificar(contrato.get("texto", ""), t) or {}
        classe = str(r.get("classificacao", AMBIGUO)).strip().lower()
        if classe not in (DENTRO, FORA, AMBIGUO):
            classe = AMBIGUO            # resposta estranha nunca vira acusação
        try:
            conf = max(0.0, min(1.0, float(r.get("confianca", 0.0))))
        except (TypeError, ValueError):
            conf = 0.0

        # ⚠️ AQUI mora o limiar assimétrico descrito no topo.
        rebaixada = False
        if classe == FORA and conf < LIMIAR_FORA:
            classe, rebaixada = AMBIGUO, True

        o = Ocorrencia(
            id=str(t.get("id", "")),
            titulo=str(t.get("titulo", "")),
            horas=float(t.get("horas") or 0),
            classificacao=classe,
            confianca=conf,
            clausula=str(r.get("clausula", ""))[:400],
            justificativa=str(r.get("justificativa", ""))[:600],
            rebaixada=rebaixada,
        )
        # ⚠️ VALOR AGORA É CALCULADO PARA TODAS, inclusive as 🟢 — mas só as
        # 🔴/🟡 entram nos totais. Uma tarefa DENTRO do escopo com 24h que
        # ninguém pediu não é cobrável, e ainda assim a agência precisa ver o
        # tamanho dela. Esconder o número porque a classe é verde apagaria
        # justamente a informação que a faria melhorar o próximo contrato.
        o.valor = _valor(o.horas, vh)
        vc = laudo.valor_contrato
        if vc > 0 and o.valor > 0:
            fatia = o.valor / vc
            o.risco = ("alto" if fatia >= RISCO_ALTO
                       else "medio" if fatia >= RISCO_MEDIO else "")
        laudo.ocorrencias.append(o)

    return laudo


def brl(v: float) -> str:
    """R$ 42.000,00 — e não `R$ 42,000.00`.

    ⚠️ Parece cosmético e não é. Este laudo é o documento que a AGÊNCIA leva
    pro cliente DELA pra sustentar um aditivo. Separador de milhar americano
    num documento de cobrança em português parece ferramenta estrangeira mal
    traduzida, e a primeira coisa que ela precisa transmitir é competência.
    """
    return ("R$ " + f"{float(v or 0):,.2f}"
            .replace(",", "\x00").replace(".", ",").replace("\x00", "."))


def num(v: float, casas: int = 1) -> str:
    """1.234,5 — mesmo motivo do `brl`, pra número que não é dinheiro.

    ⚠️ A 1ª versão fazia `f"{v:,.1f}".replace(",", ".")` e devolvia "1.234.5",
    com dois separadores iguais e nenhuma vírgula decimal. Passava despercebido
    porque os casos de teste tinham menos de mil horas."""
    return (f"{float(v or 0):,.{casas}f}"
            .replace(",", "\x00").replace(".", ",").replace("\x00", "."))


def _plural(n: int, um: str, muitos: str) -> str:
    """`1 precisa` / `2 precisam`. Concordância errada também é sinal de
    produto descuidado num documento que vai pra fora."""
    return um if n == 1 else muitos


def relatorio(laudo: Laudo) -> str:
    """O texto que a agência lê. Sem gráfico, sem dashboard — o coração."""
    L = []
    L.append(f"PROJETO: {laudo.projeto}")
    L.append(f"Valor contratado   {brl(laudo.valor_contrato):>18}")
    L.append(f"Valor-hora         {brl(laudo.valor_hora):>18}")
    L.append(f"Horas analisadas   {num(laudo.horas_totais):>18}")
    L.append("─" * 62)
    n = len(laudo.ocorrencias)
    L.append(f"{n} {_plural(n, 'tarefa analisada', 'tarefas analisadas')}")
    L.append(f"   🟢 {len(laudo.dentro):>3} dentro do escopo")
    L.append(f"   🟡 {len(laudo.ambiguas):>3} "
             f"{_plural(len(laudo.ambiguas), 'precisa', 'precisam')} "
             f"de revisão humana")
    L.append(f"   🔴 {len(laudo.fora):>3} com forte evidência de extraescopo")
    L.append("─" * 62)
    # ⚠️ A LINGUAGEM É "POTENCIALMENTE", NUNCA "O CLIENTE DEVE".
    # Quem decide se cobra é a agência, que conhece a relação com o cliente e
    # pode preferir não cobrar pra preservar a conta. O produto informa.
    L.append(f"POTENCIALMENTE FORA DO ESCOPO {brl(laudo.valor_fora):>18}")
    if laudo.ambiguas:
        L.append(f"em revisão (não somado acima) {brl(laudo.valor_ambiguo):>18}")
    L.append("")
    for o in laudo.ocorrencias:
        if o.classificacao == DENTRO:
            continue
        L.append(f"{o.cor} {o.id}  {o.titulo}"
                 + (f"   ⚠️ risco econômico {o.risco.upper()}" if o.risco else ""))
        L.append(f"     {o.horas:.1f}h × {brl(laudo.valor_hora)} = "
                 f"{brl(o.valor)}   (confiança {o.confianca:.0%})")
        if o.rebaixada:
            L.append(f"     ⚠️ evidência insuficiente pra afirmar — "
                     f"abaixo de {LIMIAR_FORA:.0%}, vai pra revisão")
        if o.clausula:
            L.append(f"     contrato: {o.clausula[:100]}")
        if o.justificativa:
            L.append(f"     por quê:  {o.justificativa[:100]}")
        if not o.horas:
            L.append(f"     ⚠️ sem horas apontadas — valor não calculado")
        L.append("")
    # ⚠️ as 🟢 grandes entram numa seção PRÓPRIA. Não são cobráveis, e são
    # exatamente o que a agência não enxerga: trabalho que ela escolheu fazer.
    _verdes_caras = [o for o in laudo.dentro if o.risco]
    if _verdes_caras:
        L.append("─" * 62)
        L.append("DENTRO DO ESCOPO, MAS CARO (não é cobrável — é pra saber):")
        for o in _verdes_caras:
            L.append(f"   🟢 {o.id}  {o.titulo[:42]}")
            L.append(f"      {o.horas:.1f}h = {brl(o.valor)} "
                     f"({100.0 * o.valor / max(1.0, laudo.valor_contrato):.0f}% "
                     f"do contrato) · risco {o.risco}")
        L.append("")
    L.append(f"cobertura decidida: {laudo.taxa_decidida:.0%} "
             f"(🟢+🔴 sobre o total — abaixo de ~60% o laudo devolve o "
             f"trabalho pro usuário)")
    return "\n".join(L)


def para_json(laudo: Laudo) -> dict:
    d = asdict(laudo)
    d.update({"valor_fora": laudo.valor_fora,
              "valor_ambiguo": laudo.valor_ambiguo,
              "taxa_decidida": laudo.taxa_decidida})
    return d
