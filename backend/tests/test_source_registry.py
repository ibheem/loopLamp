from backend.services.source_registry import SourceRegistryService


def test_source_registry_lists_sample_sources():
    service = SourceRegistryService()
    records = service.list_sources()

    assert any(record.domain == "telecom_security" for record in records)
    assert any(record.domain == "financial_risk" for record in records)
    assert any(record.domain == "medical_qa" for record in records)


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
