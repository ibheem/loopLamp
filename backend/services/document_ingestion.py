import re
import zlib
import logging
from pathlib import Path
from typing import List

import pandas as pd

from backend.core.documents import Document

logger = logging.getLogger(__name__)

try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
except Exception:  # pragma: no cover - exercised through fallback tests
    RecursiveCharacterTextSplitter = None

try:
    from pypdf import PdfReader
except Exception:  # pragma: no cover - exercised through fallback tests
    PdfReader = None


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _resolve_input_path(path: str) -> Path:
    candidate = Path(path)
    if candidate.exists():
        return candidate.resolve()

    project_candidate = PROJECT_ROOT / candidate
    if project_candidate.exists():
        return project_candidate.resolve()

    return candidate


def _fallback_chunk_text(text: str, chunk_size: int = 1000, chunk_overlap: int = 100) -> List[Document]:
    cleaned = " ".join(text.split())
    if not cleaned:
        return []

    chunks: List[Document] = []
    start = 0
    while start < len(cleaned):
        end = min(start + chunk_size, len(cleaned))
        content = cleaned[start:end].strip()
        if content:
            chunks.append(Document(page_content=content))
        if end >= len(cleaned):
            break
        start = max(0, end - chunk_overlap)
    return chunks


def _chunk_text(text: str, chunk_size: int = 1000, chunk_overlap: int = 100) -> List[Document]:
    cleaned = " ".join(text.split())
    if not cleaned:
        return []

    if RecursiveCharacterTextSplitter is not None:
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )
        chunks = [Document(page_content=chunk) for chunk in splitter.split_text(cleaned) if chunk.strip()]
        logger.info("document_chunking_strategy strategy=langchain chunks=%s", len(chunks))
        return chunks

    chunks = _fallback_chunk_text(cleaned, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    logger.info("document_chunking_strategy strategy=fallback chunks=%s", len(chunks))
    return chunks


def _decode_hex_text(hex_text: bytes) -> str:
    decoded = bytes.fromhex(hex_text.decode("ascii")).decode("utf-16-be", errors="ignore")
    chars = []
    for char in decoded:
        codepoint = ord(char)
        if codepoint == 3:
            chars.append(" ")
        elif 35 <= codepoint <= 126:
            chars.append(chr(codepoint - 3))
        else:
            chars.append(char)
    return "".join(chars)


def _extract_pdf_text_with_fallback(path: Path) -> str:
    data = path.read_bytes()
    text_parts: List[str] = []

    for match in re.finditer(rb"stream\r?\n(.*?)\r?\nendstream", data, re.S):
        try:
            decoded_stream = zlib.decompress(match.group(1))
        except zlib.error:
            continue

        for hex_text in re.findall(rb"<([0-9A-Fa-f]+)>\s*Tj", decoded_stream):
            candidate = _decode_hex_text(hex_text).strip()
            if candidate:
                text_parts.append(candidate)

    if text_parts:
        return "\n".join(text_parts)

    printable = re.findall(rb"[A-Za-z0-9][A-Za-z0-9 ,.:;@()/\-_]{4,}", data)
    return "\n".join(item.decode("latin1", errors="ignore") for item in printable)


def _extract_pdf_text(path: Path) -> str:
    if PdfReader is not None:
        try:
            reader = PdfReader(str(path))
            text = "\n".join((page.extract_text() or "") for page in reader.pages)
            cleaned = " ".join(text.split())
            if cleaned:
                logger.info("pdf_extraction_strategy strategy=pypdf source=%s", path.name)
                return text
        except Exception as exc:  # pragma: no cover - fallback exercised in tests
            logger.info(
                "pdf_extraction_strategy strategy=fallback reason=%s source=%s",
                exc.__class__.__name__,
                path.name,
            )

    logger.info("pdf_extraction_strategy strategy=manual_fallback source=%s", path.name)
    return _extract_pdf_text_with_fallback(path)


def ingest_pdf(path: str, chunk_size: int = 1000, chunk_overlap: int = 100) -> List[Document]:
    pdf_path = _resolve_input_path(path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {path}")

    text = _extract_pdf_text(pdf_path)
    chunks = _chunk_text(text, chunk_size=chunk_size, chunk_overlap=chunk_overlap)

    for index, chunk in enumerate(chunks):
        chunk.metadata.update({"source": str(pdf_path), "chunk_index": index, "file_type": "pdf"})

    return chunks


def ingest_csv(path: str) -> pd.DataFrame:
    csv_path = _resolve_input_path(path)
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV not found: {path}")

    df = pd.read_csv(csv_path)
    df.columns = [column.strip().lower().replace(" ", "_") for column in df.columns]
    df = df.drop_duplicates()
    df = df.fillna("N/A")
    return df


def csv_to_documents(df: pd.DataFrame, source: str) -> List[Document]:
    documents: List[Document] = []
    for index, row in df.iterrows():
        content = "; ".join(f"{column}: {value}" for column, value in row.items())
        documents.append(
            Document(
                page_content=content,
                metadata={"source": source, "row_index": int(index), "file_type": "csv"},
            )
        )
    return documents


def ingest_text(path: str, chunk_size: int = 1000, chunk_overlap: int = 100) -> List[Document]:
    text_path = _resolve_input_path(path)
    if not text_path.exists():
        raise FileNotFoundError(f"Text file not found: {path}")

    chunks = _chunk_text(text_path.read_text(encoding="utf-8"), chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    for index, chunk in enumerate(chunks):
        chunk.metadata.update({"source": str(text_path), "chunk_index": index, "file_type": "text"})
    return chunks


class DocumentIngestionService:
    def ingest(self, path: str) -> List[Document]:
        suffix = Path(path).suffix.lower()
        if suffix == ".pdf":
            return ingest_pdf(path)
        if suffix == ".csv":
            dataframe = ingest_csv(path)
            return csv_to_documents(dataframe, source=path)
        if suffix in {".txt", ".md"}:
            return ingest_text(path)
        raise ValueError(f"Unsupported file type: {suffix}")
