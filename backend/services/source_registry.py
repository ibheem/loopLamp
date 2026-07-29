import json
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
    ):
        self.project_root = project_root or Path(__file__).resolve().parents[2]
        self.uploads_dir = uploads_dir or self.project_root / "uploaded_sources"
        self.index_path = index_path or self.uploads_dir / "index.json"
        self.uploads_dir.mkdir(parents=True, exist_ok=True)

    def list_sources(self) -> List[SourceRecord]:
        records = self._sample_source_records() + self._uploaded_source_records()
        return sorted(records, key=lambda item: (item.domain, item.label))

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

        record = SourceRecord(
            source_id=f"upload:{stored_name}",
            label=safe_name,
            domain=domain,
            path=str(stored_path),
            file_type=stored_path.suffix.lower(),
            origin="upload",
            uploaded_at=datetime.now(timezone.utc).isoformat(),
        )
        index = self._load_upload_index()
        index[record.source_id] = record.model_dump() if hasattr(record, "model_dump") else record.dict()
        self.index_path.write_text(json.dumps(index, indent=2), encoding="utf-8")
        return record

    def delete_source(self, source_id: str) -> SourceRecord:
        if not source_id.startswith("upload:"):
            raise ValueError("Only uploaded sources can be deleted.")

        index = self._load_upload_index()
        payload = index.get(source_id)
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

        index.pop(source_id, None)
        self.index_path.write_text(json.dumps(index, indent=2), encoding="utf-8")
        return record

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
        records = []
        for payload in self._load_upload_index().values():
            record = SourceRecord(**payload)
            if Path(record.path).exists():
                records.append(record)
        return records

    def _load_upload_index(self) -> Dict[str, dict]:
        if not self.index_path.exists():
            return {}
        return json.loads(self.index_path.read_text(encoding="utf-8"))
