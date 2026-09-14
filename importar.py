#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""importar.py -- do export da agência para o formato do ESCOPO.

⚠️ POR QUE ISTO EXISTE, sendo que o trabalho sintético foi encerrado.

Não é feature. É a ponte entre um "sim" e um dado.

A agência diz sim e manda um CSV do Trello com 60 linhas. Sem isto, alguém
escreve JSON na mão, tarefa por tarefa — uma hora de trabalho chato entre o
aceite e o primeiro resultado. **É aí que piloto morre**, porque o entusiasmo de
quem topou tem prazo de validade curto.

📌 Ele também RESOLVE UM PROBLEMA DE PROTOCOLO: gera a planilha de gabarito
cego. O responsável preenche ANTES de ver qualquer saída nossa. Se ele vir
primeiro, o gabarito nasce contaminado e a medição vira teatro — pessoa que lê
"possível extraescopo, 94%" concorda muito mais do que concordaria sozinha.

    python3 importar.py tarefas.csv --contrato contrato.txt \\
        --valor 68000 --hora 200 --cliente "Agência X" --saida caso_real_01

Gera:
    dados_reais/caso_real_01.json          o caso, pronto pro avaliar.py
    dados_reais/caso_real_01_gabarito.csv  ⚠️ para o responsável preencher ANTES
"""
import argparse
import csv
import json
import re
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
DESTINO = BASE / "dados_reais"

# ⚠️ CADA FERRAMENTA CHAMA A MESMA COISA DE UM JEITO. Em vez de exigir que a
# agência renomeie colunas (atrito no pior momento possível), a gente reconhece.
COLUNAS = {
    "id": ["id", "card id", "key", "issue key", "ticket", "código", "codigo",
           "número", "numero", "short link", "card number", "task id"],
    "titulo": ["title", "titulo", "título", "name", "nome", "summary",
               "resumo", "card name", "task name", "assunto"],
    "descricao": ["description", "descricao", "descrição", "desc", "detalhes",
                  "card description", "notes", "observações", "observacoes"],
    "horas": ["horas", "hours", "time spent", "tempo", "time", "esforço",
              "esforco", "worklog", "horas trabalhadas", "logged", "spent",
              "time tracked", "duração", "duracao"],
}


def _achar(cabecalho: list, alvo: str) -> str:
    """A coluna do arquivo que corresponde a um campo nosso, sem case/acento."""
    norm = {c.strip().lower(): c for c in cabecalho if c}
    for cand in COLUNAS[alvo]:
        if cand in norm:
            return norm[cand]
    # tentativa mais frouxa: a coluna CONTÉM o termo ("Time Spent (h)")
    for cand in COLUNAS[alvo]:
        for k, original in norm.items():
            if cand in k:
                return original
    return ""


def _horas(valor: str) -> float:
    """⚠️ "12h30", "12,5", "1d 4h", "45m" — cada ferramenta escreve diferente.

    Devolve 0.0 quando não entende, e NUNCA chuta. Hora inventada vira valor
    inventado, que vira uma cobrança inventada no cliente da agência."""
    s = str(valor or "").strip().lower().replace(",", ".")
    if not s:
        return 0.0
    try:
        return max(0.0, float(s))          # "12.5"
    except ValueError:
        pass
    total = 0.0
    achou = False
    for num, unidade in re.findall(r"(\d+(?:\.\d+)?)\s*([dhm])", s):
        achou = True
        n = float(num)
        total += n * (8 if unidade == "d" else 1 if unidade == "h" else 1 / 60)
    # "12h30" sem unidade nos minutos
    m = re.fullmatch(r"(\d+)h(\d{1,2})", s)
    if m:
        return int(m.group(1)) + int(m.group(2)) / 60
    return round(total, 2) if achou else 0.0


def ler_tarefas(caminho: Path) -> tuple:
    """(tarefas, avisos). Aceita CSV e JSON."""
    avisos = []
    if caminho.suffix.lower() == ".json":
        bruto = json.loads(caminho.read_text(encoding="utf-8"))
        itens = bruto if isinstance(bruto, list) else bruto.get("tarefas", [])
        cab = list(itens[0].keys()) if itens else []
        linhas = itens
    else:
        # utf-8-sig: export de Excel vem com BOM e a 1ª coluna some do cabeçalho
        with open(caminho, encoding="utf-8-sig", newline="") as f:
            amostra = f.read(4096)
            f.seek(0)
            try:
                dial = csv.Sniffer().sniff(amostra, delimiters=",;\t")
            except csv.Error:
                dial = csv.excel          # ⚠️ arquivo estranho não pode abortar
            leitor = csv.DictReader(f, dialect=dial)
            linhas = list(leitor)
            cab = leitor.fieldnames or []

    c_id, c_tit = _achar(cab, "id"), _achar(cab, "titulo")
    c_desc, c_hrs = _achar(cab, "descricao"), _achar(cab, "horas")
    if not c_tit:
        raise SystemExit(
            f"\n❌ não achei a coluna de TÍTULO em {caminho.name}.\n"
            f"   colunas encontradas: {', '.join(cab) or '(nenhuma)'}\n"
            f"   renomeie uma para 'titulo' e rode de novo.\n")
    if not c_hrs:
        avisos.append("sem coluna de HORAS — o laudo sai sem valor em R$, "
                      "só com a classificação")

    tarefas, sem_hora = [], 0
    for i, ln in enumerate(linhas, start=1):
        tit = str(ln.get(c_tit, "")).strip()
        if not tit:
            continue                       # linha vazia de export não é tarefa
        h = _horas(ln.get(c_hrs, "")) if c_hrs else 0.0
        if c_hrs and not h:
            sem_hora += 1
        tarefas.append({
            "id": str(ln.get(c_id, "") or f"T-{i:03d}").strip(),
            "titulo": tit,
            "descricao": str(ln.get(c_desc, "") or "").strip()[:1000],
            "horas": h,
        })
    if sem_hora:
        avisos.append(f"{sem_hora} tarefa(s) com horas ilegíveis → 0.0 "
                      f"(não estimo: hora chutada vira cobrança chutada)")
    return tarefas, avisos


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("tarefas", help="CSV ou JSON exportado do Jira/Trello/etc")
    ap.add_argument("--contrato", required=True, help="arquivo .txt do contrato")
    ap.add_argument("--valor", type=float, default=0.0)
    ap.add_argument("--hora", type=float, default=0.0, help="valor-hora")
    ap.add_argument("--cliente", default="")
    ap.add_argument("--saida", default="caso_real")
    a = ap.parse_args()

    texto = Path(a.contrato).read_text(encoding="utf-8", errors="ignore").strip()
    if len(texto) < 200:
        print(f"⚠️ o contrato tem só {len(texto)} caracteres. Se veio de PDF, "
              f"talvez a extração tenha falhado — confira antes de rodar.")
    tarefas, avisos = ler_tarefas(Path(a.tarefas))

    DESTINO.mkdir(exist_ok=True)
    caso = {
        "id": a.saida,
        "descricao": "PROJETO REAL — gabarito preenchido pelo responsável.",
        "contrato": {"cliente": a.cliente or "(anonimizado)",
                     "valor": a.valor, "valor_hora": a.hora, "texto": texto},
        "tarefas": tarefas,
    }
    arq = DESTINO / f"{a.saida}.json"
    arq.write_text(json.dumps(caso, ensure_ascii=False, indent=2) + "\n",
                   encoding="utf-8")

    # ⚠️ A PLANILHA DE GABARITO NÃO TEM NENHUMA COLUNA NOSSA, de propósito.
    # Se ela trouxesse "o ESCOPO achou que...", a pessoa concordaria com a
    # sugestão em vez de pensar — e o gabarito viraria eco da nossa saída.
    gab = DESTINO / f"{a.saida}_gabarito.csv"
    with open(gab, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id", "titulo", "horas",
                    "classificacao (dentro/fora/ambiguo)",
                    "por que", "houve aditivo? (s/n)", "foi cobrado? (s/n)",
                    "quanto foi cobrado", "cliente aceitou? (s/n)",
                    "tem documento/mensagem? (s/n)"])
        for t in tarefas:
            w.writerow([t["id"], t["titulo"], t["horas"], "", "", "", "", "", "", ""])

    print(f"\n✅ {len(tarefas)} tarefa(s) importada(s)")
    for av in avisos:
        print(f"   ⚠️ {av}")
    print(f"\n   caso:     {arq.relative_to(BASE)}")
    print(f"   gabarito: {gab.relative_to(BASE)}")
    print(f"\n⚠️ A ORDEM IMPORTA, e ela é o experimento inteiro:")
    print(f"   1. mande o _gabarito.csv para o responsável preencher")
    print(f"   2. receba preenchido")
    print(f"   3. SÓ ENTÃO rode o ESCOPO")
    print(f"   Se ele vir nossa saída antes, o gabarito vira eco e a medição")
    print(f"   não mede nada.\n")
    print(f"   (dados_reais/ está no .gitignore — documento de cliente não "
          f"entra no repositório)\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
