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
