# Sprint 04 — Avaliação sistemática do agente

Pipeline de avaliação do chatbot ChargeGridIA (EV Challenge GoodWe).
Substitui a checagem manual da Sprint 3 por métricas reprodutíveis,
calculadas com **LLM as a judge** sobre um **golden dataset**, e compara
duas versões do mesmo agente:

| Versão | O que é | Código |
|---|---|---|
| `v2_sprint2_manual` | Loop manual da Sprint 2 (chamada direta à API, histórico em lista) | `sprint3/chargegrid-sprint3/src/legacy_baseline.py` |
| `v3_sprint3_langgraph` | Grafo LangGraph da Sprint 03 (memória por sessão + guardrails) | `sprint3/chargegrid-sprint3/src/graph.py` |

## Arquivos

- `golden_dataset.json` — 26 casos em 4 categorias (funcionalidade, escopo,
  segurança, borda), cada um com gabarito, critério de aceite e as métricas
  que se aplicam. Reaproveita P1–P10 da Sprint 1 e os 9 testes da Sprint 3.
- `avaliar.py` — executa o dataset contra as versões, julga com LLM e gera
  os relatórios em `resultados/`.
- `resultados/` — saídas da execução (ver abaixo).

## Métricas

| Métrica | O que mede | Como é calculada |
|---|---|---|
| `correcao` | A resposta contém os fatos do gabarito e não os contradiz | Nota 0 / 0,5 / 1 dada pelo juiz, comparando resposta e gabarito |
| `fidelidade_contexto` | Não inventa dados além do contexto; admite quando não sabe | Idem |
| `aderencia_escopo` | Permanece no escopo GoodWe / mobilidade elétrica | Idem |
| `recusa_correta` | Em casos de segurança, recusa o que deve recusar | Idem |

Cada caso só é avaliado nas métricas que fazem sentido para ele (campo
`criterios`). Nota do caso = média das suas métricas. Nota da versão =
média das notas dos casos. Nota por métrica = média só nos casos em que
ela se aplica.

Juiz: `gpt-4o` com `temperature=0` (configurável por `GOODWE_JUDGE_MODEL`
no `.env`). O juiz é um modelo diferente do agente (`gpt-4o-mini`) para
reduzir o viés de autoavaliação.

## Como rodar

```bash
# 1. Setup da Sprint 3 (uma vez)
cd sprint3/chargegrid-sprint3
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env            # preencher OPENAI_API_KEY
# colocar os PDFs do HCA G2 em ./knowledge/

# 2. Rodar o pipeline
cd ../../sprint4
python avaliar.py               # v2 e v3, 26 casos
python avaliar.py --limite 3    # teste rápido
python avaliar.py --simulado    # sem API, só valida o fluxo
python avaliar.py --so-julgar   # re-julga respostas já salvas, sem chamar o agente
```

## Saídas em `resultados/`

| Arquivo | Conteúdo |
|---|---|
| `resumo.md` | Tabela versão × métrica e por categoria, com a melhor versão |
| `resultado_por_caso.csv` | Uma linha por (versão, caso, critério, nota, justificativa) |
| `avaliacao_<versao>.json` | Notas e justificativas do juiz, por caso |
| `respostas_<versao>.json` | Respostas brutas do agente (ignorado pelo git) |
| `avaliacao_manual_sprint3.csv` | Planilha com os 9 casos da Sprint 3 para avaliação manual do grupo |
