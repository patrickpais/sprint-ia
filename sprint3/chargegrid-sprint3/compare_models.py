"""
Comparação entre modelos de linguagem - Sprint 03, seção 5 do enunciado.

Roda o MESMO conjunto de casos de teste (tests/test_cases.py) contra 2+
modelos/configurações e gera relatorio_modelos.md com os resultados brutos
de cada um lado a lado, para o grupo preencher a análise comparativa.

Como rodar (da raiz do projeto, com .env preenchido com as chaves
necessárias para cada provider que for testar):

    python compare_models.py

Edite a lista CONFIGURACOES abaixo para escolher quais modelos/parâmetros
comparar (ex: gpt-4o-mini vs gpt-4o, ou gpt-4o-mini vs um modelo Claude).
"""
from pathlib import Path

from tests.test_cases import rodar_casos

# Cada item: (nome_exibicao, provider, model_name)
# provider deve ser algo aceito por langchain.chat_models.init_chat_model
# (ex: "openai", "anthropic"). Ajuste conforme os modelos que vocês vão
# efetivamente comparar e documentar no relatório.
CONFIGURACOES = [
    ("gpt-4o-mini (OpenAI)", "openai", "gpt-4o-mini"),
    ("gpt-4o (OpenAI)", "openai", "gpt-4o"),
    # ("claude-sonnet (Anthropic)", "anthropic", "claude-sonnet-4-6"),
]


def gerar_relatorio_modelos(caminho_saida: str):
    secoes = ["# Relatório de Comparação entre Modelos - ChargeGridIA Sprint 03\n"]
    secoes.append(
        "Este relatório roda o mesmo conjunto de casos de teste "
        "(`tests/test_cases.py`) contra cada modelo/configuração listada "
        "abaixo. Preencha as seções de análise após revisar as respostas "
        "geradas.\n"
    )

    secoes.append("## Modelos avaliados\n")
    for nome, provider, model_name in CONFIGURACOES:
        secoes.append(f"- **{nome}** (`provider={provider}`, `model={model_name}`)")
    secoes.append("")

    secoes.append("## Configurações utilizadas\n")
    secoes.append(
        "- temperature: padrão do provider (ajuste em `src/graph.py` / "
        "`init_chat_model` se for comparar temperatures diferentes)\n"
        "- max_tokens / top_p: padrão do provider - documentar aqui se "
        "o grupo alterar\n"
    )

    resultados_por_modelo = {}
    for nome, provider, model_name in CONFIGURACOES:
        print(f"\n=== Rodando casos de teste com: {nome} ===")
        resultados = rodar_casos(model_provider=provider, model_name=model_name)
        resultados_por_modelo[nome] = resultados

    secoes.append("## Resultados obtidos\n")
    for nome, resultados in resultados_por_modelo.items():
        secoes.append(f"\n### {nome}\n")
        latencia_media = sum(r["latencia_total_s"] for r in resultados) / len(resultados)
        secoes.append(f"- Latência média por caso: {latencia_media:.2f}s")
        for r in resultados:
            secoes.append(f"\n**{r['id']} - {r['descricao']}**")
            for i, (turno, resposta) in enumerate(zip(r["turnos"], r["respostas"]), start=1):
                secoes.append(f"- Turno {i}: _{turno}_")
                secoes.append(f"  → {resposta}")

    secoes.append(
        "\n## Diferenças percebidas entre os modelos\n\n"
        "_(preencher após comparar as respostas acima - ex: aderência ao "
        "contexto, taxa de recusa correta nos casos de segurança, "
        "latência, custo por token)_\n"
    )
    secoes.append(
        "## Vantagens e limitações\n\n"
        "_(preencher)_\n"
    )
    secoes.append(
        "## Modelo escolhido para a versão final\n\n"
        "_(preencher - deve ser baseado nos resultados acima, não em "
        "preferência do grupo)_\n"
    )
    secoes.append(
        "## Justificativa da escolha\n\n"
        "_(preencher)_\n"
    )

    Path(caminho_saida).write_text("\n".join(secoes), encoding="utf-8")
    print(f"\nRelatório de modelos salvo em: {caminho_saida}")


if __name__ == "__main__":
    gerar_relatorio_modelos(str(Path(__file__).parent / "relatorio_modelos.md"))
