# corpus_v1 — CONGELADO em 13/09/2026

28 tarefas · 3 casos · gabarito e `prompt v1` estáveis.

## ⚠️ POR QUE CONGELAR

Sem isto acontece o seguinte, e acontece sem ninguém ter má intenção:

```
o modelo erra um caso
  ↓ "hmm, pensando bem o gabarito estava errado"
  ↓ muda o gabarito
  ↓ o modelo passa
  ↓ "96% de precisão!"
```

Isso é **benchmark por aplauso**. O número sobe, o produto não melhora, e a
comparação com execuções antigas deixa de significar qualquer coisa.

## A regra

**Não se muda gabarito porque o modelo discordou.**

Muda-se quando existe razão legítima e independente do resultado — e aí vira
`corpus_v2`, com o v1 preservado para comparação histórica.

## Uma exceção honesta já registrada

O `02/T-05` (app Android em contrato vago) está marcado `fora`, e a rodada de
13/09 sugere que `ambiguo` é a resposta melhor: o modelo seguiu a regra 6 do
nosso próprio prompt, e o gabarito é que não se sustenta nela.

📌 **Mesmo assim não foi alterado.** A razão é legítima, mas ela apareceu
*depois* de o modelo discordar — e mudar agora seria exatamente o padrão que
este arquivo existe para impedir. Fica registrado como pergunta de produto
("desproporção de esforço fura a vagueza do contrato?") para um dono de agência
responder. Se a resposta vier, vira `corpus_v2` por evidência externa, não por
conveniência.
