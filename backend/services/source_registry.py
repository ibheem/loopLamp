import json
import hashlib
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from backend.core.domain_catalog import DOMAIN_CATALOG
from backend.core.models import SourceRecord


class SourceRegistryService:
    def __init__(
        self,
        project_root: Optional[Path] = None,
        uploads_dir: Optional[Path] = None,
        index_path: Optional[Path] = None,
        db_path: Optional[Path] = None,
    ):
        self.project_root = project_root or Path(__file__).resolve().parents[2]
        self.uploads_dir = uploads_dir or self.project_root / "uploaded_sources"
        self.index_path = index_path or self.uploads_dir / "index.json"
        self.db_path = db_path or Path(self.index_path).with_suffix(".db")
        self.uploads_dir.mkdir(parents=True, exist_ok=True)
        self._ensure_database()
        self._ensure_index_state_table()
        self._migrate_legacy_index_if_needed()
        self.reconcile_uploaded_sources()

    def list_sources(self) -> List[SourceRecord]:
        records = self._sample_source_records() + self._uploaded_source_records()
        records = [self._apply_index_state(record) for record in records]
        return sorted(records, key=lambda item: (item.domain, item.label))

    def list_indexable_sources(self) -> List[SourceRecord]:
        return self.list_sources()

    def resolve_source_path(self, source_id: str) -> Path:
        for record in self.list_sources():
            if record.source_id == source_id:
                return Path(record.path)
        raise FileNotFoundError(f"Unknown source_id: {source_id}")

    def save_upload(self, filename: str, content: bytes, domain: str) -> SourceRecord:
        safe_name = Path(filename).name
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        stored_name = f"{timestamp}_{safe_name}"
        stored_path = self.uploads_dir / stored_name
        stored_path.write_bytes(content)
        content_hash = hashlib.sha256(content).hexdigest()

        record = SourceRecord(
            source_id=f"upload:{stored_name}",
            label=safe_name,
            domain=domain,
            path=str(stored_path),
            file_type=stored_path.suffix.lower(),
            origin="upload",
            uploaded_at=datetime.now(timezone.utc).isoformat(),
        )
        with self._connect() as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO uploaded_sources (
                    source_id, label, domain, path, file_type, origin, uploaded_at, content_hash
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.source_id,
                    record.label,
                    record.domain,
                    record.path,
                    record.file_type,
                    record.origin,
                    record.uploaded_at,
                    content_hash,
                ),
            )
            connection.commit()
        return record

    def delete_source(self, source_id: str) -> SourceRecord:
        if not source_id.startswith("upload:"):
            raise ValueError("Only uploaded sources can be deleted.")

        payload = self._load_upload_record(source_id)
        if payload is None:
            raise FileNotFoundError(f"Unknown source_id: {source_id}")

        record = SourceRecord(**payload)
        stored_path = Path(record.path).resolve()
        uploads_root = self.uploads_dir.resolve()
        try:
            stored_path.relative_to(uploads_root)
        except ValueError as exc:
            raise ValueError("Uploaded source path is outside the managed uploads directory.") from exc

        if stored_path.exists():
            stored_path.unlink()

        with self._connect() as connection:
            connection.execute("DELETE FROM uploaded_sources WHERE source_id = ?", (source_id,))
            connection.execute("DELETE FROM source_index_state WHERE source_id = ?", (source_id,))
            connection.commit()
        return record

    def set_source_index_state(
        self,
        source_id: str,
        index_status: str,
        vector_backend: str = "",
        indexed_document_count: Optional[int] = None,
    ):
        indexed_at = datetime.now(timezone.utc).isoformat() if index_status == "indexed" else None
        with self._connect() as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO source_index_state (
                    source_id, index_status, indexed_at, vector_backend, indexed_document_count
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    source_id,
                    index_status,
                    indexed_at,
                    vector_backend,
                    indexed_document_count,
                ),
            )
            connection.commit()

    def get_source_index_state(self, source_id: str) -> Optional[dict]:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT source_id, index_status, indexed_at, vector_backend, indexed_document_count
                FROM source_index_state
                WHERE source_id = ?
                """,
                (source_id,),
            ).fetchone()
        if row is None:
            return None
        return {
            "source_id": row["source_id"],
            "index_status": row["index_status"],
            "indexed_at": row["indexed_at"],
            "vector_backend": row["vector_backend"] or "",
            "indexed_document_count": row["indexed_document_count"],
        }

    def _sample_source_records(self) -> List[SourceRecord]:
        records: List[SourceRecord] = []
        for domain, details in DOMAIN_CATALOG.items():
            for sample_path in details.get("sample_data", []):
                full_path = self.project_root / sample_path
                if not full_path.exists():
                    continue
                records.append(
                    SourceRecord(
                        source_id=f"sample:{domain}:{full_path.name}",
                        label=full_path.name,
                        domain=domain,
                        path=str(full_path),
                        file_type=full_path.suffix.lower(),
                        origin="sample",
                    )
                )
        return records

    def _uploaded_source_records(self) -> List[SourceRecord]:
        self.reconcile_uploaded_sources()
        records = []
        for payload in self._load_upload_index().values():
            record = SourceRecord(**payload)
            if Path(record.path).exists():
                records.append(record)
        return records

    def reconcile_uploaded_sources(self) -> int:
        stale_source_ids: List[str] = []
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT source_id, path
                FROM uploaded_sources
                """
            ).fetchall()
            for row in rows:
                if not Path(row["path"]).exists():
                    stale_source_ids.append(row["source_id"])
            if stale_source_ids:
                connection.executemany(
                    "DELETE FROM uploaded_sources WHERE source_id = ?",
                    [(source_id,) for source_id in stale_source_ids],
                )
                connection.executemany(
                    "DELETE FROM source_index_state WHERE source_id = ?",
                    [(source_id,) for source_id in stale_source_ids],
                )
                connection.commit()
        return len(stale_source_ids)

    def _apply_index_state(self, record: SourceRecord) -> SourceRecord:
        state = self.get_source_index_state(record.source_id)
        if state is None:
            return record
        return record.model_copy(update=state)

    def _load_upload_index(self) -> Dict[str, dict]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT source_id, label, domain, path, file_type, origin, uploaded_at
                FROM uploaded_sources
                ORDER BY uploaded_at ASC
                """
            ).fetchall()
        return {
            row["source_id"]: {
                "source_id": row["source_id"],
                "label": row["label"],
                "domain": row["domain"],
                "path": row["path"],
                "file_type": row["file_type"],
                "origin": row["origin"],
                "uploaded_at": row["uploaded_at"],
            }
            for row in rows
        }

    def _load_upload_record(self, source_id: str) -> Optional[dict]:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT source_id, label, domain, path, file_type, origin, uploaded_at
                FROM uploaded_sources
                WHERE source_id = ?
                """,
                (source_id,),
            ).fetchone()
        if row is None:
            return None
        return {
            "source_id": row["source_id"],
            "label": row["label"],
            "domain": row["domain"],
            "path": row["path"],
            "file_type": row["file_type"],
            "origin": row["origin"],
            "uploaded_at": row["uploaded_at"],
        }

    def _ensure_database(self):
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS uploaded_sources (
                    source_id TEXT PRIMARY KEY,
                    label TEXT NOT NULL,
                    domain TEXT NOT NULL,
                    path TEXT NOT NULL,
                    file_type TEXT NOT NULL,
                    origin TEXT NOT NULL,
                    uploaded_at TEXT,
                    content_hash TEXT
                )
                """
            )
            connection.commit()

    def _ensure_index_state_table(self):
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS source_index_state (
                    source_id TEXT PRIMARY KEY,
                    index_status TEXT NOT NULL,
                    indexed_at TEXT,
                    vector_backend TEXT,
                    indexed_document_count INTEGER
                )
                """
            )
            connection.commit()

    def _migrate_legacy_index_if_needed(self):
        if not self.index_path.exists():
            return

        with self._connect() as connection:
            existing = connection.execute("SELECT COUNT(*) AS count FROM uploaded_sources").fetchone()["count"]
            if existing:
                return

        legacy_index = json.loads(self.index_path.read_text(encoding="utf-8"))
        if not legacy_index:
            return

        with self._connect() as connection:
            for payload in legacy_index.values():
                connection.execute(
                    """
                    INSERT OR REPLACE INTO uploaded_sources (
                        source_id, label, domain, path, file_type, origin, uploaded_at, content_hash
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        payload["source_id"],
                        payload["label"],
                        payload["domain"],
                        payload["path"],
                        payload["file_type"],
                        payload["origin"],
                        payload.get("uploaded_at"),
                        None,
                    ),
                )
            connection.commit()

    def _connect(self):
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection
