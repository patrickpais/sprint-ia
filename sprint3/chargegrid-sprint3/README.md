# ChargeGridIA — Sprint 03

Refatoração do núcleo conversacional do chatbot GoodWe (Sprints 1 e 2)
para usar **LangGraph** como framework de agentes, com memória de sessão
nativa, guardrails de segurança como nós do grafo, e testes automatizados
de funcionalidade, memória e segurança.

## O que mudou em relação à Sprint 2

| | Sprint 2 | Sprint 03 |
|---|---|---|
| Orquestração | Chamada direta à API OpenAI dentro de um loop `while True` | Grafo `LangGraph` (`check_input_guardrails → retrieve → generate → check_output_guardrails`) |
| Memória | Lista Python cortada manualmente (`if len(historico) > 21`) | Checkpointer nativo do LangGraph (`MemorySaver`), por `thread_id` |
| Guardrails | Só texto no system prompt | System prompt **+** nós determinísticos de checagem de entrada/saída |
| Comparação de modelos | Não existia | `compare_models.py` roda os mesmos testes em N modelos |
| RAG | Notebook Colab com download automático via `gdown` | Módulo `src/rag.py`, lê de `./knowledge/` (local) |

## Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# edite o .env com sua OPENAI_API_KEY (e ANTHROPIC_API_KEY se for comparar com Claude)
```

Coloque os PDFs/DOCX do HCA G2 e do desafio dentro de `./knowledge/`
(mesmos arquivos que estavam no Google Drive da Sprint 2).

## Rodar o chatbot

```bash
python -m src.main
```

## Rodar os casos de teste (funcional + memória + segurança)

```bash
python -m tests.test_cases
```
Gera `tests/resultados_testes.md` com o resultado de cada caso.

## Rodar o comparativo antes × depois (Sprint 2 legado vs Sprint 03)

```bash
python compare_before_after.py
```
Roda o mesmo conjunto de `tests/test_cases.py` contra uma réplica fiel do
loop manual da Sprint 2 (`src/legacy_baseline.py` - histórico em lista
cortado a cada 21 mensagens, sem grafo, sem guardrails determinísticos) e
contra o grafo novo, e gera `comparativo_antes_depois.md` com latência e
tokens/turno reais dos dois lados. Use esses números para preencher a
tabela `[preencher]` do relatório de evolução em PDF.

## Rodar a comparação entre modelos

```bash
python compare_models.py
```
Regenera `relatorio_modelos.md` com resultados reais dos modelos
configurados em `compare_models.py` (edite a lista `CONFIGURACOES` para
escolher quais comparar).

## Estrutura

```
src/
  config.py      # system prompt e configuração de modelo/paths
  rag.py         # ingestão de documentos e busca semântica
  guardrails.py  # detecção de prompt injection e checagem de escopo/saída
  graph.py       # grafo do agente + memória por sessão
  main.py        # CLI interativo (coleta LGPD, loga em JSONL)
  legacy_baseline.py  # réplica fiel do loop manual da Sprint 2 (só para comparação)
tests/
  test_cases.py  # casos funcionais, de memória e de segurança
compare_models.py
compare_before_after.py
relatorio_modelos.md
integrantes.txt
```

## Pendências para a equipe preencher antes da entrega

1. Colocar os PDFs/DOCX reais do HCA G2 em `./knowledge/` e completar
   `CONHECIMENTO_COMPLEMENTAR` em `src/rag.py` com o FAQ real usado na
   Sprint 2.
2. Rodar `python -m tests.test_cases` e `python compare_models.py` com
   as chaves de API reais para gerar os resultados de verdade.
3. Preencher `integrantes.txt` com a turma de cada integrante.
4. Preencher as seções de análise em `relatorio_modelos.md` e em
   `tests/resultados_testes.md` (o script gera as respostas brutas; a
   análise "adequado/inadequado" é uma decisão do grupo).
5. Usar os números reais (latência, tokens, resultados de segurança)
   para completar a tabela comparativa do relatório de evolução em PDF.
