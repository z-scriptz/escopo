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

## ⚠️ Quando ele diz sim e depois fica TÍMIDO

Acontece, e é onde o piloto morre. O que passa na cabeça dele:

*"contrato de cliente é confidencial, posso mandar?"* · *"vou ter que pedir
autorização?"* · *"e se for vergonhoso?"* · *"quanto trabalho isso me dá?"*

Três destravas, em ordem de eficácia:

**1. Faça junto, por chamada** — mata o medo de confidencialidade inteiro,
porque o documento nunca sai da mão dele:

> Que tal a gente ver juntos numa call de 20 minutos? Você compartilha a tela e
> eu nem preciso ficar com os arquivos. Eu só anoto as classificações e rodo
> depois com o que você autorizar.

**2. Encolha o pedido** — contrato + export + planilha é muito pra quem hesitou:

> Pra começar me manda só a cláusula do objeto — aquele parágrafo que diz o que
> foi contratado — e uns 15 títulos de tarefa. Se sair algo interessante, aí a
> gente vê o resto.

Um parágrafo e 15 linhas ele manda **hoje**, por WhatsApp. E o resultado de 15
tarefas é o que faz ele querer mandar as outras 60.

**3. Dê a garantia antes de ele pedir:**

> Compromisso: não compartilho com ninguém, não publico nada identificável, uso
> só pra validar o método, e apago em 90 dias ou quando você pedir — o que vier
> primeiro. Se preferir, troca nome do cliente e valores antes de mandar, que
> funciona igual.

## ⚠️ Enquadramento: o problema é do CONTRATO, não deles

*"Vocês deixaram R$ 18.000 na mesa"* é lido como *"vocês são desorganizados"* —
ainda mais vindo de um estudante. Ninguém quer receber isso.

> ✅ "Olha os três pontos onde a redação do contrato deixou brecha"
> ❌ "Olha o que vocês esqueceram de cobrar"

O primeiro é uma conversa que o dono **quer** ter. O segundo é uma que ele evita.

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

## Quando a resposta for SIM: o que fazer nos primeiros 10 minutos

⚠️ **Não improvise na hora.** O entusiasmo de quem topou tem prazo de validade
curto, e "me manda em outro formato" é como um piloto morre.

```bash
python3 importar.py tarefas.csv --contrato contrato.txt \
    --valor 68000 --hora 200 --cliente "Agência X" --saida real_01
```

O importador aceita CSV ou JSON de Jira, Trello, ClickUp, Notion ou planilha —
reconhece as colunas em vez de exigir que a agência renomeie nada, entende
`12h30`, `1d 4h`, `12,5` e `45m`, e **não estima hora que não entendeu** (hora
chutada vira cobrança chutada).

Ele gera DOIS arquivos:

```
dados_reais/real_01.json           o caso
dados_reais/real_01_gabarito.csv   ⚠️ para o responsável preencher ANTES
```

**A ordem é o experimento inteiro:**

```
1. manda o _gabarito.csv         ← sem NADA da nossa saída dentro
2. recebe preenchido
3. SÓ ENTÃO roda o ESCOPO
4. compara
```

📌 A planilha de gabarito não tem nenhuma coluna nossa, de propósito. Se
trouxesse "o ESCOPO achou que…", a pessoa concordaria com a sugestão em vez de
pensar, e o gabarito viraria eco. Ela também já pede o nível A: houve aditivo?
foi cobrado? quanto? o cliente aceitou? tem documento?

## O que vira dataset

```
tarefa
  ↓ resposta do ESCOPO        (classe · confiança · cláusula citada)
  ↓ resposta do responsável   (dentro / fora / discutível)
  ↓ evidência documental      (aditivo? cobrança? mensagem?)
  ↓ resultado comercial       (cobrou? aceitaram? quanto?)
```

Com algumas dezenas disso dá pra responder o que hoje é palpite:

- o `LIMIAR_FORA = 0.93` **provisório** se sustenta? (escolhido em 10 acusações
  sintéticas — recalibrar com ≥100 tarefas reais e ≥20 🔴 reais)
- "confiança 0,93" corresponde a quantos por cento de acerto real? (a tabela de
  calibração existe; falta dado real pra preencher)
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
