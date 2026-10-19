"""
Guardrails do ChargeGridIA.

Na Sprint 2, as regras de segurança viviam só dentro do system prompt
(esperando que o modelo obedecesse). Na Sprint 03 elas viram uma camada
explícita e testável, aplicada ANTES do modelo gerar a resposta (nó
`check_input_guardrails` do grafo) e reforçada DEPOIS (nó
`check_output_guardrails`), reduzindo a dependência de o LLM "se lembrar"
de seguir a instrução.

Isso não substitui o system prompt (a defesa em profundidade continua
usando os dois), mas dá uma segunda camada determinística que não pode
ser sobrescrita por texto do usuário.
"""
import re

# --- Detecção de tentativas de Prompt Injection -----------------------
# Lista de padrões comuns de tentativa de jailbreak/instruction override.
# Não é exaustiva (não existe filtro 100% robusto baseado em regex), mas
# cobre os vetores mais comuns e serve de primeira barreira antes do LLM.
_PADROES_INJECTION = [
    r"ignore\s+(todas\s+)?(as\s+)?(suas\s+)?instru[cç][oõ]es",
    r"esque[çc]a\s+(todas\s+)?(as\s+)?(suas\s+)?instru[cç][oõ]es",
    r"disregard\s+(all\s+)?(previous|prior)\s+instructions",
    r"ignore\s+(all\s+)?(previous|prior)\s+instructions",
    r"revele?\s+(o\s+)?(seu\s+)?system\s*prompt",
    r"mostre?\s+(o\s+)?(seu\s+)?system\s*prompt",
    r"(qual|quais)\s+(s[ãa]o?\s+)?(suas?\s+)?instru[çc][ãa]o(es)?\s+(interna|original)",
    r"voc[êe]\s+n[ãa]o\s+(trabalha|é)\s+mais\s+(para|da)",
    r"a\s+partir\s+de\s+agora\s+voc[êe]\s+[ée]",
    r"finja\s+que\s+voc[êe]\s+([ée]|n[ãa]o)",
    r"modo\s+desenvolvedor",
    r"\bdan\b.{0,15}(mode|modo)",
    r"act\s+as\s+if\s+you\s+(are|have)\s+no\s+restrictions",
]

_REGEX_INJECTION = re.compile("|".join(_PADROES_INJECTION), flags=re.IGNORECASE)


def detectar_prompt_injection(texto: str) -> bool:
    """Retorna True se o texto do usuário contém padrão típico de tentativa
    de sobrescrever instruções do sistema."""
    return bool(_REGEX_INJECTION.search(texto))


# --- Checagem de escopo -------------------------------------------------
# Palavras-chave que indicam que a pergunta está dentro do domínio
# GoodWe/mobilidade elétrica. É uma checagem leniente e barata (regex),
# usada só como sinal auxiliar - a decisão final de escopo continua
# reforçada pelo system prompt; o objetivo aqui é logar/testar, não
# bloquear perguntas legítimas de forma agressiva.
_PALAVRAS_ESCOPO = [
    "goodwe", "hca", "carregador", "carga", "carregamento", "eletroposto",
    "veículo elétrico", "veiculo eletrico", "ev ", "ocpp", "condomínio",
    "condominio", "wallbox", "tomada", "bateria", "mobilidade elétrica",
]


def possivelmente_fora_de_escopo(texto: str) -> bool:
    texto_lower = texto.lower()
    return not any(p in texto_lower for p in _PALAVRAS_ESCOPO)


# --- Checagem de conselhos sensíveis na SAÍDA do modelo ------------------
_PADROES_CONSELHO_JURIDICO = re.compile(
    r"(na\s+minha\s+opini[ãa]o\s+jur[íi]dica|legalmente\s+voc[êe]\s+deve|"
    r"como\s+seu\s+advogado|isso\s+configura\s+crime)",
    re.IGNORECASE,
)
_PADROES_CONSELHO_FINANCEIRO = re.compile(
    r"(voc[êe]\s+deve\s+investir|garanto\s+retorno|como\s+seu\s+consultor\s+financeiro)",
    re.IGNORECASE,
)


def resposta_contem_conselho_sensivel(texto: str) -> str | None:
    """Retorna o tipo de conselho sensível detectado na resposta do
    modelo, ou None se não encontrar nada. Serve como rede de segurança
    adicional (o ideal é que o system prompt já evite isso)."""
    if _PADROES_CONSELHO_JURIDICO.search(texto):
        return "juridico"
    if _PADROES_CONSELHO_FINANCEIRO.search(texto):
        return "financeiro"
    return None


MENSAGEM_BLOQUEIO_INJECTION = (
    "Não posso ignorar minhas instruções nem revelar meu system prompt ou "
    "funcionamento interno. Posso te ajudar com dúvidas sobre o carregador "
    "GoodWe HCA G2, eletropostos e mobilidade elétrica - como posso ajudar "
    "nesse tema?"
)

MENSAGEM_CONSELHO_JURIDICO = (
    "Não posso te orientar juridicamente como se fosse um advogado. "
    "Recomendo consultar um profissional do direito para avaliar essa "
    "situação. Posso te ajudar com o que for relacionado ao carregador "
    "GoodWe ou ao funcionamento do eletroposto, se quiser."
)

MENSAGEM_CONSELHO_FINANCEIRO = (
    "Não posso te dar uma recomendação financeira como se fosse um "
    "consultor financeiro. Recomendo conversar com um profissional da área "
    "para avaliar o investimento com base na sua situação. Posso te ajudar "
    "com informações técnicas sobre os carregadores GoodWe, se for útil."
)
