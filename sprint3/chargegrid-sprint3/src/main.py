"""
Chatbot interativo ChargeGridIA - Sprint 03.

Mantém a mesma experiência de usuário da Sprint 2 (coleta opcional de
dados com consentimento LGPD, log de conversas em JSONL), mas a memória
da conversa agora é 100% responsabilidade do grafo/checkpointer do
LangGraph - `thread_id` = sessao_id.
"""
import json
import re
import uuid
from datetime import datetime

from .graph import build_graph, perguntar


def validar_email(email: str) -> bool:
    return bool(re.match(r"^[\w\.-]+@[\w\.-]+\.\w{2,}$", email))


def coletar_email() -> str:
    while True:
        email = input("E-mail: ").strip()
        if validar_email(email):
            return email
        print("  Email invalido. Exemplo: nome@email.com")


def perguntar_sim_nao(mensagem: str) -> str:
    while True:
        resposta = input(mensagem).strip().lower()
        if resposta in ["sim", "s"]:
            return "sim"
        if resposta in ["não", "nao", "n"]:
            return "nao"
        print('  Nao entendi. Digite "sim" ou "nao".')


def coletar_dados_usuario():
    print("=" * 60)
    print("   ChargeGridIA - FIAP EV Challenge 2026 (Sprint 03)")
    print("=" * 60)
    print(
        "\nOla! Bem-vindo ao suporte GoodWe.\n"
        "\nGostariamos de convidar voce a compartilhar alguns dados para "
        "acompanhamento da sua solicitacao. Caso aceite, pedimos: nome e e-mail.\n"
        "\nLGPD: seus dados sao coletados com base na Lei no 13.709/2018 e "
        "usados exclusivamente para este atendimento.\n"
    )
    resposta = perguntar_sim_nao("Deseja compartilhar seus dados? (sim/nao): ")

    dados = {"compartilhou_dados": False, "nome": None, "email": None}
    if resposta == "sim":
        dados["compartilhou_dados"] = True
        dados["nome"] = input("\nNome completo: ").strip()
        dados["email"] = coletar_email()
        nome_exibicao = dados["nome"].split()[0]
    else:
        apelido = input("\nSem problemas! Como posso te chamar? ").strip()
        dados["nome"] = apelido
        nome_exibicao = apelido

    print(f"\nOi, {nome_exibicao}! Em que posso te ajudar? (digite 'sair' para encerrar)")
    print("-" * 60)
    return dados, nome_exibicao


def registrar_turno(log_path: str, sessao_id: str, pergunta: str, resposta: str):
    linha = {
        "sessao_id": sessao_id,
        "timestamp": datetime.now().isoformat(),
        "pergunta": pergunta,
        "resposta": resposta,
    }
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(linha, ensure_ascii=False) + "\n")


def main():
    from . import config

    graph = build_graph()
    dados_usuario, nome_exibicao = coletar_dados_usuario()
    sessao_id = str(uuid.uuid4())

    while True:
        pergunta = input(f"\n{nome_exibicao}: ").strip()
        if not pergunta:
            continue
        if pergunta.lower() in ("sair", "encerrar", "exit", "quit"):
            print(f"\nAte logo, {nome_exibicao}! Obrigado por usar o ChargeGridIA.")
            break

        resposta = perguntar(graph, thread_id=sessao_id, pergunta=pergunta)
        print(f"\nAssistente: {resposta}")
        registrar_turno(config.LOG_PATH, sessao_id, pergunta, resposta)


if __name__ == "__main__":
    main()
