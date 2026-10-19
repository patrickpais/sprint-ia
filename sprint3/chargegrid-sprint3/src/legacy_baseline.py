"""
Baseline "legado" - réplica fiel da arquitetura da Sprint 2, para servir
de ponto de comparação real na seção 6 do enunciado (comparativo antes x
depois). NÃO é código de produção da Sprint 03 - existe só para gerar
métricas comparáveis (latência, tokens/turno) contra o mesmo conjunto de
testes rodado no grafo novo.

Reproduz deliberadamente as características da Sprint 2 que a Sprint 03
corrigiu:
- Chamada direta ao client da OpenAI, sem framework de agentes.
- Histórico mantido numa lista Python, cortado manualmente após 21 msgs.
- Guardrails apenas como texto no system prompt (sem nós determinísticos).
"""
import time

from openai import OpenAI

from . import config, rag

MAX_HISTORICO = 21  # mesmo valor usado no notebook da Sprint 2


class ChatLegado:
    """Uma instância = uma sessão de conversa, no estilo Sprint 2."""

    def __init__(self, vector_store=None, model_name: str = "gpt-4o-mini"):
        self.client = OpenAI()
        self.model_name = model_name
        self.historico: list[dict] = []
        self.vector_store = vector_store or rag.build_vector_store()

    def perguntar(self, pergunta: str) -> tuple[str, float]:
        contexto = rag.buscar_contexto(self.vector_store, pergunta)

        mensagens = [{"role": "system", "content": config.SYSTEM_PROMPT}]
        if contexto:
            mensagens.append({"role": "system", "content": f"Contexto:\n{contexto}"})
        mensagens.extend(self.historico)
        mensagens.append({"role": "user", "content": pergunta})

        inicio = time.monotonic()
        resposta = self.client.chat.completions.create(
            model=self.model_name,
            messages=mensagens,
        )
        latencia = time.monotonic() - inicio
        texto_resposta = resposta.choices[0].message.content

        # Gerenciamento manual de histórico - exatamente como na Sprint 2.
        self.historico.append({"role": "user", "content": pergunta})
        self.historico.append({"role": "assistant", "content": texto_resposta})
        if len(self.historico) > MAX_HISTORICO:
            self.historico = self.historico[-MAX_HISTORICO:]

        return texto_resposta, latencia
