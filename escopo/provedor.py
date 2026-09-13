#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""provedor.py -- o LLM atrás de uma interface. NENHUM ID de modelo no código.

⚠️ POR QUE O MODELO NÃO PODE ESTAR CRAVADO AQUI.

Em algumas semanas vamos querer rodar Gemini caro × Gemini barato × Claude ×
GPT contra o MESMO gabarito, e responder com número:

    modelo caro     96% precisão / 78% cobertura
    modelo barato   94% precisão / 77% cobertura   ← produção usa este

Se o ID estiver espalhado pelo código, essa comparação vira refatoração.

⚠️ E TEM UM MOTIVO MAIS IMEDIATO: eu não tenho como verificar, escrevendo isto,
que um dado ID de modelo existe. Meu conhecimento tem corte, modelos são
lançados e descontinuados, e cravar um identificador que eu não confirmei é
exatamente a classe de erro que já custou caro neste projeto.

📌 Então o ID vem do ambiente e é VALIDADO CONTRA A API antes do primeiro uso.
Quem diz se o modelo existe é o provedor, não a minha lembrança.
"""
import json
import os
import time
import urllib.error
import urllib.request

TEMPO_LIMITE = int(os.environ.get("ESCOPO_TIMEOUT", "60"))


class ErroProvedor(RuntimeError):
    pass


class Resposta:
    """O que todo provedor devolve, igual, pro resto do código não saber qual é."""

    def __init__(self, dados: dict, tokens_entrada=0, tokens_saida=0,
                 duracao=0.0, modelo="", cru=""):
        self.dados = dados or {}
        self.tokens_entrada = int(tokens_entrada or 0)
        self.tokens_saida = int(tokens_saida or 0)
        self.duracao = round(float(duracao or 0), 3)
        self.modelo = modelo
        self.cru = cru


class Provedor:
    nome = "base"

    def modelos(self) -> list:
        raise NotImplementedError

    def validar_modelo(self) -> str:
        """⚠️ Falha CEDO e com a lista na mão. Descobrir que o modelo não existe
        no meio de uma avaliação de 200 chamadas é perder a rodada inteira."""
        disponiveis = self.modelos()
        if not disponiveis:
            return ""                     # API não listou; seguimos e o erro virá
        if self.modelo in disponiveis:
            return self.modelo
        parecidos = [m for m in disponiveis if self.modelo.split("-")[0] in m][:8]
        raise ErroProvedor(
            f"modelo '{self.modelo}' não existe nesta conta/API.\n"
            f"  Parecidos disponíveis: {', '.join(parecidos) or '(nenhum)'}\n"
            f"  Corrija CLASSIFIER_MODEL no .env.")

    def gerar(self, prompt: str, schema: dict) -> Resposta:
        raise NotImplementedError


class Gemini(Provedor):
    nome = "gemini"
    BASE = "https://generativelanguage.googleapis.com/v1beta"

    def __init__(self, modelo: str = "", chave: str = ""):
        self.modelo = (modelo or os.environ.get("CLASSIFIER_MODEL", "")).strip()
        self.chave = (chave or os.environ.get("GEMINI_API_KEY", "")).strip()
        if not self.chave:
            raise ErroProvedor(
                "GEMINI_API_KEY ausente. Ponha no .env da máquina — "
                "nunca no código, nunca colada no chat.")
        if not self.modelo:
            raise ErroProvedor("CLASSIFIER_MODEL ausente no .env.")

    def _http(self, url: str, corpo: dict = None) -> dict:
        dados = json.dumps(corpo).encode() if corpo is not None else None
        req = urllib.request.Request(
            url, data=dados,
            headers={"Content-Type": "application/json",
                     "x-goog-api-key": self.chave},
            method="POST" if corpo is not None else "GET")
        try:
            with urllib.request.urlopen(req, timeout=TEMPO_LIMITE) as r:
                return json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            # ⚠️ o CORPO do erro é o que diz o motivo; o código sozinho não.
            # Mesma lição do `(#3)` da Meta, que passou meses truncado no log.
            try:
                detalhe = e.read().decode()[:400]
            except Exception:
                detalhe = ""
            raise ErroProvedor(f"HTTP {e.code} — {detalhe}") from None
        except Exception as e:
            raise ErroProvedor(f"{type(e).__name__}: {str(e)[:200]}") from None

    def modelos(self) -> list:
        """O que ESTA conta realmente pode chamar. Fonte da verdade."""
        try:
            d = self._http(f"{self.BASE}/models")
        except ErroProvedor:
            return []
        nomes = []
        for m in d.get("models", []):
            n = (m.get("name") or "").replace("models/", "")
            if "generateContent" in (m.get("supportedGenerationMethods") or []):
                nomes.append(n)
        return sorted(nomes)

    def gerar(self, prompt: str, schema: dict) -> Resposta:
        corpo = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                # ⚠️ saída estruturada: nada de parsear texto livre e rezar
                "responseMimeType": "application/json",
                "responseSchema": schema,
                # determinismo importa — a mesma tarefa tem que dar a mesma
                # resposta, senão a medição não é reprodutível
                "temperature": 0,
            },
        }
        t0 = time.time()
        d = self._http(f"{self.BASE}/models/{self.modelo}:generateContent", corpo)
        dt = time.time() - t0

        texto = ""
        for c in d.get("candidates", []):
            for p in (c.get("content") or {}).get("parts", []):
                texto += p.get("text", "")
        try:
            dados = json.loads(texto) if texto.strip() else {}
        except json.JSONDecodeError:
            dados = {}              # resposta ilegível vira 🟡 lá no motor
        u = d.get("usageMetadata") or {}
        return Resposta(dados,
                        tokens_entrada=u.get("promptTokenCount", 0),
                        tokens_saida=u.get("candidatesTokenCount", 0),
                        duracao=dt, modelo=self.modelo, cru=texto[:2000])


class Dublê(Provedor):
    """Provedor falso pra teste: sem rede, resposta programada."""
    nome = "dublê"

    def __init__(self, respostas=None, modelo="dublê-1", disponiveis=None):
        self.respostas = respostas or {}
        self.modelo = modelo
        # ⚠️ A LISTA É INDEPENDENTE DO MODELO ESCOLHIDO, e isso é o ponto.
        # A 1ª versão fazia `modelos() -> [self.modelo]`: qualquer ID que eu
        # escolhesse "existia" por definição, e a validação passava sempre.
        # Validação que nunca reprova não é validação — é decoração que dá
        # confiança falsa, que é pior que não ter nenhuma.
        self.disponiveis = list(disponiveis) if disponiveis is not None \
            else [modelo]
        self.chamadas = []

    def modelos(self):
        return list(self.disponiveis)

    def gerar(self, prompt, schema):
        self.chamadas.append(prompt)
        for chave, r in self.respostas.items():
            if chave in prompt:
                return Resposta(r, 10, 5, 0.01, self.modelo)
        return Resposta({}, 10, 5, 0.01, self.modelo)


def criar(nome: str = "") -> Provedor:
    nome = (nome or os.environ.get("CLASSIFIER_PROVIDER", "gemini")).lower()
    if nome == "gemini":
        return Gemini()
    if nome in ("dublê", "duble", "fake"):
        return Dublê()
    # ⚠️ Claude e GPT entram aqui quando formos comparar. O resto do código
    # não muda uma linha — é pra isso que esta função existe.
    raise ErroProvedor(f"provedor '{nome}' não implementado (tenho: gemini, dublê)")
