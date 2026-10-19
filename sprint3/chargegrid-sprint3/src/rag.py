"""
Ingestão de documentos e busca semântica (RAG).

Mantém a mesma lógica de fontes da Sprint 2 (PDFs do HCA G2, docs do
desafio, FAQ complementar hardcoded, scraping opcional do site GoodWe),
mas isolada em funções reutilizáveis pelo grafo de agente da Sprint 03,
em vez de células soltas de notebook.

Para rodar localmente: coloque os PDFs/DOCX em ./knowledge/ antes de
chamar build_vector_store(). O scraping do site e a transcrição de vídeo
(Whisper) são opcionais e desativados por padrão (ver USE_WEB_SCRAPING /
USE_VIDEO_TRANSCRIPTION abaixo) porque dependem de rede/API extra.
"""
import glob
import os

from langchain_core.documents import Document
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from . import config

USE_WEB_SCRAPING = os.getenv("GOODWE_USE_WEB_SCRAPING", "false").lower() == "true"

# FAQ complementar - respostas garantidas independentemente do que foi
# capturado via scraping/PDF (mesma ideia da Sprint 2, seção 5d do notebook).
# Edite/complete esta lista com o conteúdo real usado pelo grupo.
CONHECIMENTO_COMPLEMENTAR = [
    {
        "titulo": "LED e notificação de fim de carregamento - HCA G2",
        "conteudo": (
            "GoodWe HCA G2 - Como saber quando o carro terminou de carregar.\n"
            "Indicações do LED durante a sessão:\n"
            "- LED branco pulsante: aguardando conexão do veículo (standby)\n"
            "- LED azul fixo/pulsante: carregando\n"
            "- LED verde fixo: carga concluída\n"
            "(Ajuste este texto para refletir o manual real do HCA G2 usado pelo grupo.)"
        ),
    },
]


def _carregar_pdfs() -> list[Document]:
    caminhos = glob.glob(os.path.join(config.KNOWLEDGE_DIR, "**", "*.pdf"), recursive=True)
    docs: list[Document] = []
    if not caminhos:
        print("[rag] Nenhum PDF encontrado em ./knowledge - RAG usará apenas o FAQ complementar.")
        return docs
    from langchain_community.document_loaders import PyPDFLoader

    for caminho in caminhos:
        try:
            docs.extend(PyPDFLoader(caminho).load())
        except Exception as e:
            print(f"[rag] Falha ao carregar {caminho}: {e}")
    return docs


def _carregar_docx() -> list[Document]:
    caminhos = glob.glob(os.path.join(config.KNOWLEDGE_DIR, "**", "*.docx"), recursive=True)
    docs: list[Document] = []
    if not caminhos:
        return docs
    from langchain_community.document_loaders import Docx2txtLoader

    for caminho in caminhos:
        try:
            docs.extend(Docx2txtLoader(caminho).load())
        except Exception as e:
            print(f"[rag] Falha ao carregar {caminho}: {e}")
    return docs


def _carregar_faq() -> list[Document]:
    return [
        Document(page_content=item["conteudo"], metadata={"titulo": item["titulo"], "fonte": "faq"})
        for item in CONHECIMENTO_COMPLEMENTAR
    ]


def _carregar_web() -> list[Document]:
    if not USE_WEB_SCRAPING:
        return []
    from langchain_community.document_loaders import RecursiveUrlLoader
    from bs4 import BeautifulSoup

    def extrair_texto(html: str) -> str:
        return BeautifulSoup(html, "lxml").get_text(" ", strip=True)

    try:
        loader = RecursiveUrlLoader(
            url="https://br.goodwe.com/",
            max_depth=2,
            extractor=extrair_texto,
        )
        return loader.load()
    except Exception as e:
        print(f"[rag] Falha no scraping do site: {e}")
        return []


def carregar_documentos() -> list[Document]:
    docs = _carregar_pdfs() + _carregar_docx() + _carregar_faq() + _carregar_web()
    print(f"[rag] Total de documentos carregados: {len(docs)}")
    return docs


def build_vector_store() -> InMemoryVectorStore:
    docs = carregar_documentos()
    embeddings = OpenAIEmbeddings(model=config.EMBEDDING_MODEL)
    vector_store = InMemoryVectorStore(embeddings)

    if not docs:
        return vector_store

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        add_start_index=True,
    )
    chunks = splitter.split_documents(docs)
    vector_store.add_documents(chunks)
    print(f"[rag] {len(chunks)} trechos indexados no vector store.")
    return vector_store


def buscar_contexto(vector_store: InMemoryVectorStore, pergunta: str, k: int = 4) -> str:
    if vector_store is None:
        return ""
    resultados = vector_store.similarity_search(pergunta, k=k)
    return "\n\n".join(doc.page_content for doc in resultados)
