# ESCOPO

ESCOPO — auditor inteligente que cruza contratos e entregas para identificar
trabalho fora do escopo, calcular valores não cobrados e transformar esforço
perdido em receita recuperável.

> **Descubra quanto trabalho sua empresa fez de graça.**

Agência ou software house fecha um projeto por R$ 42.000. Durante quatro meses o
cliente vai pedindo *"já que vocês estão mexendo, coloca isso aqui"*. Ninguém
abre aditivo. No fim, foram entregues R$ 58.000 de trabalho por R$ 42.000.

---

    python3 teste_motor.py        # motor determinístico, sem rede

| | |
|---|---|
| `docs/PRODUTO.md` | o que a v0.1 é, o que ela **não** é, e as regras que não se negociam |
| `escopo/motor.py` | limiar, conta e agregação. **Nenhum número sai de LLM** |
| `casos/` | corpus sintético com gabarito humano e o **porquê** de cada resposta |
| `teste_motor.py` | testa o MOTOR (o classificador é dublê; a qualidade da IA se mede à parte) |

## As três regras

**1. A IA interpreta. O código calcula.** O modelo devolve classificação,
cláusula e confiança — nunca valor. Hora × valor-hora, soma e limiar são
determinísticos.

**2. O limiar é assimétrico.** `fora` exige ≥85% de confiança; `dentro` não
exige nada. Errar pra menos custa dinheiro que a agência já perdia. Errar pra
mais custa a **confiança** dela com o cliente — e isso não volta.

**3. Cobertura é métrica de primeira classe.** Se quase tudo cair em 🟡, a
agência recebeu uma lista de "sei lá" e faz o trabalho na mão, que é o que ela
já fazia de graça. **Precisão sem cobertura não é produto.**

## Estado

Motor + corpus sintético, 41 asserções verdes. Sem interface, sem LLM ligado,
sem dados reais. O próximo passo é o classificador, pra medir **precisão** e
**cobertura** contra o gabarito.

⚠️ **O risco do projeto não é construir — é uma empresa entregar contrato e
tarefas de um projeto real.** Esse é o recurso escasso, e ele vem antes do
produto ficar pronto.
