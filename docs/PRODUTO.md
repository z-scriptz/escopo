# ESCOPO — v0.1

> Descubra quanto trabalho sua empresa fez de graça.

Agência ou software house fecha um projeto por R$ 42.000. Durante quatro meses o
cliente vai pedindo *"já que vocês estão mexendo, coloca isso aqui"*. Ninguém
abre aditivo. No fim, foram entregues R$ 58.000 de trabalho por R$ 42.000.

O ESCOPO lê o contrato, lê as tarefas executadas, e mostra o que ficou fora.

---

## O que a v0.1 faz

```
contrato (texto)  +  tarefas (id, título, descrição, horas)  +  valor-hora
        ↓
  extração do escopo contratual        ← LLM
        ↓
  classificação tarefa × escopo        ← LLM
        ↓
  limiar · conta · agregação           ← código
        ↓
  🟢 dentro   🟡 revisão humana   🔴 forte evidência de extraescopo
  + cláusula relacionada, horas, valor potencial, confiança
```

## O que a v0.1 NÃO faz

Sem login, sem dashboard, sem multiempresa, sem integração com Jira/GitHub/Slack,
sem geração de aditivo, sem banco de dados, sem upload de PDF. **Nada disso entra
antes de o motor acertar.** Interface bonita em cima de classificação ruim é o
jeito mais caro de descobrir que o produto não funciona.

## As três regras que não se negociam

**1. A IA interpreta. O código calcula.**
O modelo devolve `{"classificacao": "fora", "clausula": "...", "confianca": 0.91}`.
Ele nunca devolve valor. Hora × valor-hora, soma e limiar são determinísticos —
um número alucinado dentro de uma cobrança que a agência leva pro cliente dela
acaba com o produto no primeiro uso.

**2. Precisão acima de cobertura, de forma assimétrica.**
Errar para menos custa dinheiro que a agência já perdia. Errar para mais custa a
**confiança**: ela leva uma cobrança de R$ 3.000 pro cliente, o cliente mostra a
cláusula, e ela nunca mais abre a ferramenta. Então `fora` precisa de evidência
forte (≥ 85%) e `dentro` não precisa de nada. Um 🔴 fraco vira 🟡.

**3. A linguagem é "potencialmente", nunca "o cliente deve".**
Quem decide se cobra é a agência — ela conhece a relação e pode preferir não
cobrar pra preservar a conta. O produto informa; não acusa.

## As duas métricas

| métrica | o que é | por que importa |
|---|---|---|
| **precisão** | dos 🔴, quantos o humano confirma | um falso positivo queima a confiança |
| **cobertura** | fração em 🟢/🔴 (não 🟡) | se quase tudo cai em 🟡, a agência recebeu uma lista de "sei lá" e faz o trabalho na mão — que é o que ela já fazia de graça |

**Precisão sem cobertura não é produto.** As duas são medidas juntas, sempre.

Alvo pra considerar o motor utilizável: **cobertura ≥ 60%** com **precisão ≥ 90%**
nos 🔴, medido contra gabarito humano.

## O risco real do projeto

Não é construir. É **uma empresa entregar contrato e tarefas de um projeto real**.

Esse é o recurso escasso — do mesmo jeito que alcance orgânico era o recurso
escasso no projeto anterior, e a gente passou cinco meses construindo máquina
assumindo que a distribuição apareceria.

**Então o primeiro documento real vem antes do produto ficar pronto**, não depois.
Dado sintético serve pra construir o motor; não serve pra provar nada.

## Modelo comercial (v0)

Primeiros 3–5 pilotos **gratuitos**, em troca de dados reais, validação humana das
detecções e permissão de usar resultados anonimizados. Depois, mensalidade única
(~R$ 499) — não três planos.

Success fee fica como hipótese futura: "recuperado" é difícil de medir (a agência
pode detectar R$ 8.000 e decidir não cobrar pra preservar o cliente, cobrar só
parte, ou receber 90 dias depois).

## Depois da v0.1, se ela funcionar

- **ESCOPO Guard** — tarefa nova entra no board, compara com o contrato **antes**
  da execução: *"possível extraescopo, 94% — gerar aditivo?"*
- **ESCOPO Change Order** — transforma a detecção em documento de aditivo
- **ESCOPO Intelligence** — com centenas de projetos: *"esse cliente pede 31% mais
  fora de escopo que a média"*

Nada disso entra no MVP. Está aqui pra lembrar que a arquitetura não deve
impedir — não pra ser construído agora.
