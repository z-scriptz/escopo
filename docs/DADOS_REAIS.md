# Protocolo de coleta — primeiro projeto real

> ⚠️ **Este documento vale mais que o corpus sintético.** O motor está pronto, a
> medição está pronta, o modelo real já rodou. O gargalo do projeto deixou de
> ser engenharia e virou **conseguir dados**.

O corpus sintético foi escrito por quem também escreveu o gabarito. Ele pega
falha grosseira e detecta regressão. **Ele não valida nada.** Validação é uma
agência olhando o laudo e dizendo *"caralho, realmente fizemos isso e não
cobramos"*.

---

## A regra que não pode ser quebrada: coleta CEGA

```
1. recebemos contrato + tarefas
2. o responsável classifica dentro / fora / ambíguo  ← SEM ver nossa saída
3. só então o ESCOPO classifica
4. só então comparamos
```

⚠️ **Se ele vir o resultado antes, o gabarito está contaminado** e a medição
inteira vira teatro. Pessoa que lê *"possível extraescopo, 94%"* concorda com
muito mais frequência do que concordaria sozinha. Não é desonestidade — é como
funciona.

📌 Na prática: peça a classificação dele **antes de rodar qualquer coisa**, e
guarde a resposta antes de abrir o terminal.

## Hierarquia de evidência

Duas pessoas da mesma agência discordam: o PM diz que estava fora, o dev diz que
estava dentro, o comercial acha que vendeu junto. Por isso nem toda resposta vale
o mesmo.

| nível | o que é | peso |
|---|---|---|
| **A — fato documental** | aditivo aprovado, change request, orçamento extra enviado, cobrança feita, mensagem explícita (*"isso não está contemplado, precisa de orçamento"*) | **ouro** |
| **B — avaliação humana** | o responsável classifica hoje, olhando para trás | bom |
| **C — modelo** | o ESCOPO decide | é o que estamos medindo |

Quando A e B divergem, **A ganha**. Opinião retrospectiva é reconstrução; documento
é registro do que se pensava na hora.

## O que pedir

**Um projeto JÁ ENCERRADO.** Reduz sensibilidade, o desfecho é conhecido, e
ninguém está arriscando uma negociação em andamento.

```
1 contrato assinado           (PDF ou texto)
30–100 tarefas                (export do Jira/Trello/ClickUp/Notion, CSV ou JSON)
horas por tarefa              (se existirem — se não, o valor não é calculado)
valor do contrato e valor-hora
```

**Anonimização — ofereça as três, nessa ordem:**

- **A** — dados reais completos
- **B** — contrato com nome do cliente e valores trocados por marcadores
- **C** — só a estrutura: cláusulas e títulos de tarefa, sem nada identificável

O C ainda serve. **Peça o que a pessoa estiver confortável em dar** — o pior
resultado é ela não dar nada porque o pedido pareceu grande demais.

## Como abrir a conversa

Não comece por *"me manda seu contrato"*. Comece pela pesquisa:

> Estou desenvolvendo meu TCC sobre detecção automática de trabalho fora de
> escopo em projetos de software. Estou procurando projetos **já encerrados**
> para validar o método — comparo o contrato com as tarefas executadas e
> identifico o que pode ter ficado fora.
>
> Se vocês toparem, devolvo gratuitamente o relatório do que eu encontrar. O
> material pode vir anonimizado, e eu não preciso de valores reais.

📌 Ninguém entrega documento pra um vendedor. Quase todo mundo ajuda um
estudante. **E é verdade** — não é técnica de venda, é o que está acontecendo.

## As perguntas, depois do gabarito cego

Faça **nesta ordem**, e só depois de ter a classificação dele.

**Sobre cada tarefa marcada como fora ou discutível:**

1. Isso estava dentro, fora, ou era discutível?
2. Houve aditivo? Change request? Orçamento extra?
3. Chegou a ser cobrado? Quanto?
4. O cliente aceitou?
5. Existe mensagem, e-mail ou documento que comprove?
6. Se não cobraram — por quê? (Preservar a relação? Esqueceram? Acharam pequeno?)

**Sobre o projeto:**

7. Quanto vocês acham que deixaram de faturar nesse projeto?
8. Vocês descobriram isso durante ou só no fim?
9. O que fariam diferente no contrato?

⚠️ A pergunta 6 é a que mais ensina sobre o produto. Se a resposta for *"a gente
preferiu não cobrar"*, então o ESCOPO não pode ser uma ferramenta de cobrança —
tem que ser uma ferramenta de **decisão informada**. Muda o texto do laudo, muda
o pitch, muda tudo.

## O que vira dataset

```
tarefa
  ↓ resposta do ESCOPO        (classe · confiança · cláusula citada)
  ↓ resposta do responsável   (dentro / fora / discutível)
  ↓ evidência documental      (aditivo? cobrança? mensagem?)
  ↓ resultado comercial       (cobrou? aceitaram? quanto?)
```

Com algumas dezenas disso dá pra responder o que hoje é palpite:

- o `LIMIAR_FORA = 0.85` está certo, ou deveria ser 0.95? (**hipótese H1**,
  levantada na rodada de 13/09 e ainda não testada)
- "confiança 0,93" corresponde a quantos por cento de acerto real?
- que tipo de tarefa gera mais extraescopo?
- que redação de contrato produz mais ambiguidade?

## Marco

```
5 projetos · 100–200 tarefas reais · classificadas às cegas
```

Não precisa vir tudo de uma vez. **O primeiro projeto já muda o estado do
negócio** — é a diferença entre "experimento tecnicamente interessante" e
"alguém confirmou que isso acha dinheiro de verdade".

## ⚠️ Segurança, desde o primeiro arquivo

Contrato de empresa é documento sensível, mesmo encerrado.

- `dados_reais/` e `execucoes/` estão no `.gitignore` — **confira antes de
  colocar o primeiro arquivo lá** (`git check-ignore -v dados_reais/x.pdf`)
- nada de documento de cliente colado em chat, issue ou commit
- quando o projeto tiver cliente de verdade: chave de API própria, não a
  compartilhada com outros projetos
