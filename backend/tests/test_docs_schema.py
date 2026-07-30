from backend.app.main import app
from backend.core.models import DashboardResponse
from backend.core.models import QueryRequest
from backend.core.models import UploadSourceRequest


def test_query_request_schema_contains_real_examples():
    if hasattr(QueryRequest, "model_json_schema"):
        schema = QueryRequest.model_json_schema()
    else:
        schema = QueryRequest.schema()

    examples = schema.get("examples") or schema.get("example") or []
    serialized = str(examples)

    assert "test_data/telecom_incident.txt" in serialized
    assert "telecom_security" in serialized
    assert "What action is recommended for the SS7 issue?" in serialized


def test_upload_source_request_schema_contains_real_examples():
    if hasattr(UploadSourceRequest, "model_json_schema"):
        schema = UploadSourceRequest.model_json_schema()
    else:
        schema = UploadSourceRequest.schema()

    examples = schema.get("examples") or schema.get("example") or []
    serialized = str(examples)

    assert "field_notes.txt" in serialized
    assert "medical_qa" in serialized
    assert "content_base64" in serialized


def test_openapi_sources_endpoints_include_examples():
    schema = app.openapi()

    upload_request_examples = schema["components"]["schemas"]["UploadSourceRequest"]["examples"]
    upload_serialized = str(upload_request_examples)
    assert "field_notes.txt" in upload_serialized
    assert "medical_case_summary.json" in upload_serialized

    delete_parameters = schema["paths"]["/sources/{source_id}"]["delete"]["parameters"]
    source_id_parameter = next(parameter for parameter in delete_parameters if parameter["name"] == "source_id")
    assert source_id_parameter["schema"]["examples"] == ["upload:20260728061500_field_notes.txt"]

    source_list_example = schema["components"]["schemas"]["SourceListResponse"]["example"]
    assert source_list_example["sources"][0]["origin"] == "sample"
    assert source_list_example["sources"][1]["origin"] == "upload"


def test_dashboard_response_schema_contains_domain_examples():
    if hasattr(DashboardResponse, "model_json_schema"):
        schema = DashboardResponse.model_json_schema()
    else:
        schema = DashboardResponse.schema()

    examples = schema.get("examples") or []
    serialized = str(examples)

    assert "telecom_security" in serialized
    assert "financial_risk" in serialized
    assert "medical_qa" in serialized
    assert "banking_assistant" in serialized
    assert "automotive" in serialized
    assert "manufacturing" in serialized
    assert "ecommerce" in serialized
    assert "Telecom Security Dashboard Report" in serialized


def test_openapi_dashboard_endpoint_includes_examples():
    schema = app.openapi()

    dashboard_examples = schema["components"]["schemas"]["DashboardResponse"]["examples"]
    serialized = str(dashboard_examples)

    assert "Telecom Security Dashboard Report" in serialized
    assert "Financial Risk Dashboard Report" in serialized
    assert "Medical Qa Dashboard Report" in serialized
    assert "Banking Assistant Dashboard Report" in serialized
    assert "Automotive Dashboard Report" in serialized
    assert "Manufacturing Dashboard Report" in serialized
    assert "Ecommerce Dashboard Report" in serialized
    assert "matched_sources" in serialized
    assert "evidence_cards" in serialized
    assert "domain_cards" in serialized
