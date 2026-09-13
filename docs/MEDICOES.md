# Medições

Toda rodada registrada aqui. ⚠️ **Nenhum número deste arquivo é validação de
produto** — o corpus é sintético e escrito por quem também escreveu o gabarito.
Serve pra pegar falha grosseira e detectar regressão ao trocar modelo/prompt.

---

## 13/09/2026 · gemini-3.8-flash · prompt v1 · corpus sintético (16 tarefas)

```
concordância 88%  (14/16)

🔴 precisão            80%      ⚠️ FALSO VERMELHO 20%   FPR 9%
🟢 precisão           100%      dinheiro perdido   0%
cobertura              75%      taxa 🟡           25%

trap      3/3  100%   ← as armadilhas passaram
hard      2/2  100%
easy      6/6  100%
ambiguous 3/4   75%
medium    0/1    0%

770 tokens entrada/tarefa · 3,7s/tarefa
```

**O sinal bom:** as três armadilhas passaram — filtro já contratado, correção de
bug, reunião de alinhamento. É onde um sistema ingênuo acusa errado e queima a
agência com o cliente dela.

### ⚠️ A calibração diz algo concreto sobre o limiar

```
0.95–1.00   n=10  acertou 100%
0.90–0.95   n=4   acertou  75%
0.85–0.90   n=2   acertou  50%
```

Monotônica. E a única ACUSAÇÃO INDEVIDA da rodada saiu a 90%:

```
T-06  "Exportar relatório em PDF"   nós: fora @90%   gabarito: ambiguo
```

Os quatro 🔴 corretos saíram em 95–98%. **Com `LIMIAR_FORA=0.95` a acusação
indevida some e os corretos ficam**, custando ~6 pontos de cobertura.

📌 **NÃO MEXIDO.** Ajustar parâmetro olhando 16 amostras — com **n=2** na faixa
decisiva — é ajustar ao ruído. Hipótese registrada para testar com dado real.
`LIMIAR_FORA=0.85` segue sendo palpite, e segue anotado como palpite.

### ⚠️ O segundo erro provavelmente é do gabarito, não do modelo

```
T-05  "App Android" em contrato vago   nós: ambiguo @85%   gabarito: fora
```

O gabarito (meu) diz `fora` porque 90h de app nativo num contrato de R$ 18k é
desproporção que fala por si. O modelo disse `ambiguo` **seguindo a regra 6 do
nosso próprio prompt**, que manda cair em ambíguo quando o contrato é vago.

Ele obedeceu a instrução; o gabarito é que não se sustenta nela.

**Pergunta de produto em aberto, para um dono de agência responder:**
desproporção de esforço deve furar a vagueza do contrato?

### O que esta rodada NÃO prova

16 tarefas, 5 🔴. Um erro move a precisão em 20 pontos. O relatório avisa isso
antes dos números de propósito. E o gabarito é meu — então "80% de precisão"
quer dizer *"o Gemini concordou comigo 80% das vezes"*.


---

## 13/09/2026 · caso 03 (zona cinzenta) · gemini-3.8-flash · prompt v1

```
9/12 · cobertura 75% · 🔴 precisão 60% (3 acusações indevidas)

trap      3/3  100%      ambiguous 2/4   50%
medium    2/2  100%      hard      2/3   67%
```

### ⚠️ O teste mais duro do corpus passou

```
T-06  bug 40 dias após a entrega   → dentro (98%)
T-07  bug 140 dias após a entrega  → fora   (95%)     vigência: 90 dias
```

Mesma natureza, mesma redação, **só a data muda**. Ele leu o prazo e fez a
conta — não reconheceu o formato da frase.

E as armadilhas: **6/6 somando as duas rodadas**. Não caiu no "checkout" do
campo CPF, não cobrou o responsivo quebrado, e não sugeriu faturar 24h de
refatoração que a própria agência escolheu fazer.

### Os três erros estão todos no mesmo lugar

```
T-09 treinamento      ambiguo → fora   @88%   ACUSAÇÃO INDEVIDA
T-10 blog por e-mail  ambiguo → fora   @90%   ACUSAÇÃO INDEVIDA
T-04 frete            fora → ambiguo   @80%
```

Os dois falsos vermelhos são **ausência tratada como exclusão**. ⚠️ E é a
segunda vez que eu desconfio do meu próprio gabarito depois de o modelo
discordar — o que é exatamente o motivo de o corpus estar congelado.

---

## DECISÃO · `LIMIAR_FORA` 0.85 → **0.93** (provisório)

Somando as duas rodadas: **28 tarefas, 10 acusações.**

```
🔴 CERTOS  (7)   95 · 95 · 95 · 95 · 95 · 98 · 98
🔴 ERRADOS (3)   88 · 90 · 90
```

**Separação limpa, sem sobreposição.** E a hipótese H1 foi registrada na rodada
dos casos 01+02, **antes de o caso 03 existir** — então o caso 03 é dado
independente, não ajuste ao ruído.

O replay (`relimiar.py`, custo zero):

| limiar | 🔴 precisão | indevidas | cobertura |
|---|---|---|---|
| 0.85 | 70% | **30%** | 75% |
| 0.93 | **100%** | 0% | 64% |
| 0.98 | 100% | 0% | 46% |

**A troca é de produto, e é deliberada:** 1 em cada 3 tarefas indo pra revisão
humana é ruim. 1 em cada 3 cobranças chegando errada no cliente da agência
**acaba com o produto** — ela não abre a ferramenta uma segunda vez.

📌 **0.93 e não 0.95.** Resultado idêntico hoje, mas 0.95 fica em cima do menor
acerto observado; um acerto futuro a 94% se perderia. 0.93 fica no meio da faixa
limpa, com margem dos dois lados.

⚠️ **NÃO é limiar validado.** 10 acusações, corpus sintético, gabarito de quem
escreveu o corpus. Recalibrar só com **≥100 tarefas reais rotuladas às cegas** e
**≥20 casos 🔴 reais** — e mesmo aí será avaliação inicial.

**Trabalho sintético encerrado aqui.** Corpus v1 congelado, prompt v1 congelado,
limiar provisório escolhido. O gargalo agora é dado real.
