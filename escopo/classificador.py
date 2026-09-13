#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""classificador.py -- o LLM lê contrato + tarefa e classifica. Só isso.

⚠️ O QUE ELE NÃO FAZ, E NUNCA VAI FAZER: calcular valor. Ele devolve
classificação, cláusula, justificativa e confiança. Hora × valor-hora é do
`motor.py`. Um número alucinado dentro de uma cobrança que a agência leva pro
cliente dela acaba com o produto no primeiro uso.

📌 O PROMPT É VERSIONADO. Toda avaliação registra qual versão rodou — senão,
daqui a um mês, "melhorou?" volta a ser respondido com *"acho que sim"*.
"""
PROMPT_VERSAO = "v1"

# ⚠️ Schema rígido: o modelo não escolhe o formato da resposta.
SCHEMA = {
    "type": "object",
    "properties": {
        "classificacao": {"type": "string",
                          "enum": ["dentro", "fora", "ambiguo"]},
        "clausula": {"type": "string"},
        "justificativa": {"type": "string"},
        "confianca": {"type": "number"},
    },
    "required": ["classificacao", "clausula", "justificativa", "confianca"],
}

# ⚠️ AS INSTRUÇÕES SÃO ASSIMÉTRICAS DE PROPÓSITO — é a tese do produto escrita
# em português pro modelo. Errar pra menos custa dinheiro que a agência já
# perdia. Errar pra mais custa a confiança dela com o cliente, e isso não volta.
INSTRUCOES = """Você analisa se uma tarefa executada estava dentro do escopo \
contratado de um projeto de software.

Responda com UMA destas classificações:

- "dentro": o contrato cobre esta tarefa, explícita ou razoavelmente.
- "fora": o contrato claramente NÃO cobre, ou a exclui nominalmente.
- "ambiguo": o contrato não permite decidir com segurança.

REGRAS QUE VALEM MAIS QUE SUA IMPRESSÃO GERAL:

1. "fora" é uma ACUSAÇÃO. Ela vai virar uma cobrança que a empresa apresenta \
ao cliente dela. Se o cliente puder apontar uma cláusula que cobre a tarefa, a \
empresa perde credibilidade e para de usar este sistema. Só use "fora" quando \
você conseguir citar o trecho do contrato que sustenta a exclusão, ou a \
ausência inequívoca do item no objeto.

2. Na dúvida, "ambiguo" — nunca "fora". Deixar passar custa pouco; acusar \
errado custa a relação.

3. CORREÇÃO DE DEFEITO em funcionalidade já entregue é "dentro", sempre, mesmo \
que dê muito trabalho. Bug não é escopo novo.

4. REUNIÃO, ALINHAMENTO, GESTÃO e comunicação são custo de conduzir o projeto, \
não entrega ampliada. Classifique como "dentro", a menos que o contrato diga \
o contrário.

5. Detalhe de algo que JÁ ESTÁ no objeto é "dentro". Se o contrato diz \
"relatórios com filtros", adicionar um filtro é o que foi contratado — não é \
pedido novo.

6. Se o contrato for vago ou remeter a documento que você não recebeu \
("conforme proposta anexa"), quase tudo vira "ambiguo". Não preencha a lacuna \
com o que parece razoável: o documento é que decide, e ele não está aqui.

7. Quantidade escrita no contrato é limite. "Três níveis de permissão" torna o \
quarto nível uma ampliação decidível.

confianca: 0.0 a 1.0. Quão seguro você está DESTA classificação. Seja \
conservador: acima de 0.85 significa que você citaria o trecho do contrato \
numa discussão com o cliente e se sustentaria.

clausula: o trecho LITERAL do contrato em que você se baseou. Se não houver \
trecho aplicável, escreva "nenhum trecho aplicável" — não invente citação.

justificativa: uma frase. Por que esta classificação e não outra."""


def montar_prompt(contrato: str, tarefa: dict) -> str:
    t = tarefa or {}
    return (
        f"{INSTRUCOES}\n\n"
        f"===== CONTRATO =====\n{(contrato or '').strip()}\n\n"
        f"===== TAREFA EXECUTADA =====\n"
        f"Título: {t.get('titulo', '')}\n"
        f"Descrição: {t.get('descricao', '')}\n\n"
        # ⚠️ HORAS FICAM FORA DO PROMPT DE PROPÓSITO.
        # Saber que a tarefa levou 90h enviesa o modelo a achar que é grande e
        # portanto extraescopo. Tamanho não é escopo: uma tarefa contratada
        # pode ser enorme e uma fora do escopo pode levar 20 minutos. As horas
        # entram depois, no motor, só pra calcular valor.
        f"Classifique esta tarefa."
    )


def classificar_com(provedor):
    """Devolve a função `classificar(contrato, tarefa)` que o motor injeta.

    A última resposta crua fica em `.ultima` pra o avaliador registrar tokens,
    duração e modelo sem que o motor precise saber que LLM existe."""
    def classificar(contrato: str, tarefa: dict) -> dict:
        r = provedor.gerar(montar_prompt(contrato, tarefa), SCHEMA)
        classificar.ultima = r
        return r.dados
    classificar.ultima = None
    classificar.versao = PROMPT_VERSAO
    return classificar
