"""
Comparativo antes x depois - Sprint 03, seção 6 do enunciado.

Roda o MESMO conjunto de casos de teste (tests/test_cases.py) contra:
  (a) o baseline legado (src/legacy_baseline.py - réplica da Sprint 2)
  (b) o grafo novo da Sprint 03 (src/graph.py)

e gera comparativo_antes_depois.md com métricas reais: latência total,
tokens por turno (via tiktoken) e as respostas lado a lado, para
substituir os "[preencher]" do relatório de evolução por números de
verdade.

Como rodar (da raiz do projeto, com .env preenchido):
    python compare_before_after.py
"""
import uuid
from pathlib import Path

import tiktoken

from src.legacy_baseline import ChatLegado
from src.graph import build_graph, perguntar
from tests.test_cases import CASOS

try:
    _ENC = tiktoken.encoding_for_model("gpt-4o-mini")
except Exception:
    _ENC = tiktoken.get_encoding("cl100k_base")


def contar_tokens(texto: str) -> int:
    return len(_ENC.encode(texto or ""))


def rodar_legado() -> list[dict]:
    resultados = []
    for caso in CASOS:
        chat = ChatLegado()
        respostas, latencias, tokens_totais = [], [], 0
        for turno in caso.turnos:
            resposta, latencia = chat.perguntar(turno)
            respostas.append(resposta)
            latencias.append(latencia)
            tokens_totais += contar_tokens(turno) + contar_tokens(resposta)
        resultados.append({
            "id": caso.id, "categoria": caso.categoria, "descricao": caso.descricao,
            "turnos": caso.turnos, "respostas": respostas,
            "latencia_total_s": round(sum(latencias), 2),
            "tokens_totais": tokens_totais,
        })
        print(f"[legado] {caso.id} ok")
    return resultados


def rodar_sprint03() -> list[dict]:
    graph = build_graph()
    resultados = []
    for caso in CASOS:
        thread_id = str(uuid.uuid4())
        respostas, tokens_totais = [], 0
        import time
        inicio = time.monotonic()
        for turno in caso.turnos:
            resposta = perguntar(graph, thread_id=thread_id, pergunta=turno)
            respostas.append(resposta)
            tokens_totais += contar_tokens(turno) + contar_tokens(resposta)
        latencia = time.monotonic() - inicio
        resultados.append({
            "id": caso.id, "categoria": caso.categoria, "descricao": caso.descricao,
            "turnos": caso.turnos, "respostas": respostas,
            "latencia_total_s": round(latencia, 2),
            "tokens_totais": tokens_totais,
        })
        print(f"[sprint03] {caso.id} ok")
    return resultados


def gerar_markdown(legado: list[dict], novo: list[dict], caminho: str):
    linhas = ["# Comparativo Antes x Depois - ChargeGridIA\n"]
    linhas.append(
        "| Caso | Categoria | Latência legado (s) | Latência Sprint 03 (s) | "
        "Tokens legado | Tokens Sprint 03 |"
    )
    linhas.append("|---|---|---|---|---|---|")
    total_lat_legado = total_lat_novo = total_tok_legado = total_tok_novo = 0
    for r_leg, r_novo in zip(legado, novo):
        linhas.append(
            f"| {r_leg['id']} | {r_leg['categoria']} | {r_leg['latencia_total_s']} | "
            f"{r_novo['latencia_total_s']} | {r_leg['tokens_totais']} | {r_novo['tokens_totais']} |"
        )
        total_lat_legado += r_leg["latencia_total_s"]
        total_lat_novo += r_novo["latencia_total_s"]
        total_tok_legado += r_leg["tokens_totais"]
        total_tok_novo += r_novo["tokens_totais"]

    n = len(legado)
    linhas.append(
        f"| **Média** | | {round(total_lat_legado / n, 2)} | {round(total_lat_novo / n, 2)} | "
        f"{round(total_tok_legado / n)} | {round(total_tok_novo / n)} |"
    )

    linhas.append("\n## Respostas lado a lado (para checar qualidade manualmente)\n")
    for r_leg, r_novo in zip(legado, novo):
        linhas.append(f"### {r_leg['id']} - {r_leg['descricao']}")
        for i, turno in enumerate(r_leg["turnos"]):
            linhas.append(f"- Turno {i+1}: _{turno}_")
        linhas.append(f"- **Legado:** {r_leg['respostas'][-1]}")
        linhas.append(f"- **Sprint 03:** {r_novo['respostas'][-1]}\n")

    linhas.append(
        "\n> Nota: tokens contados com tiktoken (aproximação - o valor exato "
        "pode variar por provider/modelo). Latência inclui a chamada ao "
        "vector store (RAG) em ambas as versões.\n"
    )
    Path(caminho).write_text("\n".join(linhas), encoding="utf-8")
    print(f"\nComparativo salvo em: {caminho}")


if __name__ == "__main__":
    print("=== Rodando baseline legado (Sprint 2) ===")
    resultados_legado = rodar_legado()
    print("\n=== Rodando Sprint 03 (framework de agentes) ===")
    resultados_novo = rodar_sprint03()
    gerar_markdown(resultados_legado, resultados_novo, str(Path(__file__).parent / "comparativo_antes_depois.md"))
