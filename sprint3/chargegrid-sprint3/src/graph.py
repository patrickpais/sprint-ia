"""
Núcleo conversacional do ChargeGridIA - Sprint 03.

Principal mudança em relação à Sprint 2:
- Sprint 2: o pipeline LangGraph (retrieve -> generate) só era usado nos
  testes isolados; o chatbot interativo de verdade chamava a API da OpenAI
  direto, com histórico gerenciado numa lista Python cortada manualmente
  (`if len(historico) > 21: ...`).
- Sprint 03: existe um ÚNICO grafo, com estado persistido por sessão via
  checkpointer do LangGraph (`thread_id`). Não há mais corte manual de
  lista - a memória é responsabilidade do framework. Guardrails de entrada
  e saída viram nós explícitos do grafo, não só texto no system prompt.

Fluxo do grafo:
    START -> check_input_guardrails -> [bloqueado?] -> refuse -> END
                                      -> retrieve -> generate -> check_output_guardrails -> END
"""
from typing import Annotated, Literal, TypedDict

from langchain.chat_models import init_chat_model
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages

from . import config, guardrails, rag


class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    context: str
    guardrail_flag: str  # "ok" | "injection"
    fora_de_escopo_sinalizado: bool  # sinal auxiliar, não bloqueante (ver check_input_guardrails)


def build_graph(model_provider: str | None = None, model_name: str | None = None):
    """Constrói e compila o grafo do agente.

    model_provider/model_name permitem sobrescrever o modelo em tempo de
    execução - usado pelo harness de comparação de modelos (Sprint 03,
    seção 5 do enunciado) sem duplicar o grafo inteiro.
    """
    provider = model_provider or config.MODEL_PROVIDER
    name = model_name or config.MODEL_NAME

    llm = init_chat_model(name, model_provider=provider)
    vector_store = rag.build_vector_store()

    def check_input_guardrails(state: AgentState) -> AgentState:
        ultima_msg = state["messages"][-1]
        texto = ultima_msg.content if isinstance(ultima_msg.content, str) else str(ultima_msg.content)

        # Sinal auxiliar de escopo: é leniente de propósito (ver guardrails.py),
        # então NÃO bloqueia sozinho - só fica registrado no estado para
        # aparecer nos logs/testes e permitir auditoria do comportamento do
        # agente (requisito da seção 4 do enunciado: "permanece dentro do
        # contexto do projeto GoodWe"). A defesa real de escopo continua
        # sendo o system prompt + a checagem de prompt injection abaixo.
        fora_de_escopo = guardrails.possivelmente_fora_de_escopo(texto)
        if fora_de_escopo:
            print(f"[guardrail_entrada] Pergunta sinalizada como possivelmente fora de escopo: {texto!r}")

        if guardrails.detectar_prompt_injection(texto):
            return {"guardrail_flag": "injection", "fora_de_escopo_sinalizado": fora_de_escopo}

        return {"guardrail_flag": "ok", "fora_de_escopo_sinalizado": fora_de_escopo}

    def route_after_guardrails(state: AgentState) -> Literal["refuse", "retrieve"]:
        return "refuse" if state["guardrail_flag"] == "injection" else "retrieve"

    def refuse(state: AgentState) -> AgentState:
        return {"messages": [AIMessage(content=guardrails.MENSAGEM_BLOQUEIO_INJECTION)]}

    def retrieve(state: AgentState) -> AgentState:
        ultima_msg = state["messages"][-1]
        pergunta = ultima_msg.content if isinstance(ultima_msg.content, str) else str(ultima_msg.content)
        contexto = rag.buscar_contexto(vector_store, pergunta)
        return {"context": contexto}

    def generate(state: AgentState) -> AgentState:
        historico = state["messages"]
        contexto = state.get("context", "")

        mensagens = [SystemMessage(content=config.SYSTEM_PROMPT)]
        if contexto:
            mensagens.append(SystemMessage(content=f"Contexto recuperado dos documentos:\n{contexto}"))
        mensagens.extend(historico)

        resposta = llm.invoke(mensagens)
        return {"messages": [resposta]}

    def check_output_guardrails(state: AgentState) -> AgentState:
        ultima_msg = state["messages"][-1]
        texto = ultima_msg.content if isinstance(ultima_msg.content, str) else str(ultima_msg.content)
        tipo = guardrails.resposta_contem_conselho_sensivel(texto)
        if tipo is None:
            return {}

        # Guardrail de saída ATIVO: se a resposta do modelo escapou pelo
        # system prompt e soou como conselho jurídico/financeiro
        # profissional, substitui a resposta por uma versão segura em vez
        # de só logar. Isso é a segunda camada de defesa (o ideal é que o
        # system prompt já evite isso na maioria dos casos).
        print(f"[guardrail_saida] Resposta bloqueada - continha conselho tipo '{tipo}'. Substituindo por resposta segura.")
        mensagem_segura = (
            guardrails.MENSAGEM_CONSELHO_JURIDICO
            if tipo == "juridico"
            else guardrails.MENSAGEM_CONSELHO_FINANCEIRO
        )
        # Usa o mesmo id da mensagem original para que o reducer add_messages
        # SUBSTITUA a resposta problemática no histórico, em vez de só
        # anexar a versão segura ao lado dela - assim a memória da sessão
        # não guarda o conselho indevido para turnos futuros.
        return {"messages": [AIMessage(content=mensagem_segura, id=ultima_msg.id)]}

    builder = StateGraph(AgentState)
    builder.add_node("check_input_guardrails", check_input_guardrails)
    builder.add_node("refuse", refuse)
    builder.add_node("retrieve", retrieve)
    builder.add_node("generate", generate)
    builder.add_node("check_output_guardrails", check_output_guardrails)

    builder.add_edge(START, "check_input_guardrails")
    builder.add_conditional_edges(
        "check_input_guardrails",
        route_after_guardrails,
        {"refuse": "refuse", "retrieve": "retrieve"},
    )
    builder.add_edge("refuse", END)
    builder.add_edge("retrieve", "generate")
    builder.add_edge("generate", "check_output_guardrails")
    builder.add_edge("check_output_guardrails", END)

    checkpointer = MemorySaver()
    return builder.compile(checkpointer=checkpointer)


def perguntar(graph, thread_id: str, pergunta: str) -> str:
    """Envia uma pergunta ao agente dentro de uma sessão (thread_id) e
    retorna a resposta. A memória da conversa é gerenciada pelo
    checkpointer do LangGraph - não é preciso reenviar o histórico."""
    config_execucao = {"configurable": {"thread_id": thread_id}}
    resultado = graph.invoke({"messages": [HumanMessage(content=pergunta)]}, config=config_execucao)
    return resultado["messages"][-1].content
