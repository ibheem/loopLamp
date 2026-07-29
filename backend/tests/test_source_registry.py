from backend.services.source_registry import SourceRegistryService


def test_source_registry_lists_sample_sources():
    service = SourceRegistryService()
    records = service.list_sources()

    assert any(record.domain == "telecom_security" for record in records)
    assert any(record.domain == "financial_risk" for record in records)
    assert any(record.domain == "medical_qa" for record in records)
    assert any(record.domain == "banking_assistant" for record in records)
    assert any(record.domain == "automotive" for record in records)
    assert any(record.domain == "manufacturing" for record in records)
    assert any(record.domain == "ecommerce" for record in records)


def test_source_registry_can_save_upload(tmp_path):
    uploads_dir = tmp_path / "uploads"
    index_path = uploads_dir / "index.json"
    service = SourceRegistryService(project_root=tmp_path, uploads_dir=uploads_dir, index_path=index_path)

    record = service.save_upload(
        filename="note.txt",
        content=b"uploaded source content",
        domain="general",
    )

    assert record.origin == "upload"
    assert record.label == "note.txt"
    assert service.resolve_source_path(record.source_id).exists()


def test_source_registry_persists_upload_metadata_in_sqlite(tmp_path):
    uploads_dir = tmp_path / "uploads"
    index_path = uploads_dir / "index.json"
    service = SourceRegistryService(project_root=tmp_path, uploads_dir=uploads_dir, index_path=index_path)

    record = service.save_upload(
        filename="persisted_note.txt",
        content=b"persisted source content",
        domain="general",
    )

    reloaded = SourceRegistryService(project_root=tmp_path, uploads_dir=uploads_dir, index_path=index_path)
    records = reloaded.list_sources()

    assert any(item.source_id == record.source_id for item in records)


def test_source_registry_applies_persisted_index_state(tmp_path):
    uploads_dir = tmp_path / "uploads"
    index_path = uploads_dir / "index.json"
    service = SourceRegistryService(project_root=tmp_path, uploads_dir=uploads_dir, index_path=index_path)

    record = service.save_upload(
        filename="indexed_note.txt",
        content=b"persisted source content",
        domain="general",
    )
    service.set_source_index_state(
        source_id=record.source_id,
        index_status="indexed",
        vector_backend="qdrant_persistent",
        indexed_document_count=4,
    )

    reloaded = SourceRegistryService(project_root=tmp_path, uploads_dir=uploads_dir, index_path=index_path)
    indexed = next(item for item in reloaded.list_sources() if item.source_id == record.source_id)

    assert indexed.index_status == "indexed"
    assert indexed.vector_backend == "qdrant_persistent"
    assert indexed.indexed_document_count == 4
    assert indexed.indexed_at is not None


def test_source_registry_can_delete_upload(tmp_path):
    uploads_dir = tmp_path / "uploads"
    index_path = uploads_dir / "index.json"
    service = SourceRegistryService(project_root=tmp_path, uploads_dir=uploads_dir, index_path=index_path)

    record = service.save_upload(
        filename="note.txt",
        content=b"uploaded source content",
        domain="general",
    )

    deleted = service.delete_source(record.source_id)

    assert deleted.source_id == record.source_id
    try:
        service.resolve_source_path(record.source_id)
    except FileNotFoundError:
        pass
    else:
        raise AssertionError("Expected deleted upload to be removed from the registry.")


def test_source_registry_rejects_sample_deletion():
    service = SourceRegistryService()

    try:
        service.delete_source("sample:telecom_security:telecom_incident.txt")
    except ValueError as exc:
        assert str(exc) == "Only uploaded sources can be deleted."
    else:
        raise AssertionError("Expected sample source deletion to be rejected.")


def test_source_registry_reconciles_stale_uploaded_metadata(tmp_path):
    uploads_dir = tmp_path / "uploads"
    index_path = uploads_dir / "index.json"
    service = SourceRegistryService(project_root=tmp_path, uploads_dir=uploads_dir, index_path=index_path)

    record = service.save_upload(
        filename="stale_note.txt",
        content=b"stale source content",
        domain="general",
    )
    stored_path = service.resolve_source_path(record.source_id)
    stored_path.unlink()

    reloaded = SourceRegistryService(project_root=tmp_path, uploads_dir=uploads_dir, index_path=index_path)
    records = reloaded.list_sources()

    assert all(item.source_id != record.source_id for item in records)
    try:
        reloaded.resolve_source_path(record.source_id)
    except FileNotFoundError:
        pass
    else:
        raise AssertionError("Expected stale upload metadata to be removed from the registry.")
