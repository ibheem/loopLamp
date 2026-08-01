from pathlib import Path

from backend.app.main import app
from backend.core.models import DashboardResponse
from backend.core.models import LLMProviderCatalogResponse
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
    assert "llm_provider" in serialized
    assert "openai" in serialized
    assert "llm_model" in serialized


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


def test_llm_provider_catalog_schema_contains_examples():
    if hasattr(LLMProviderCatalogResponse, "model_json_schema"):
        schema = LLMProviderCatalogResponse.model_json_schema()
    else:
        schema = LLMProviderCatalogResponse.schema()

    example = schema.get("example") or {}
    serialized = str(example)

    assert "default_provider_id" in serialized
    assert "openai" in serialized
    assert "gpt-5-mini" in serialized
    assert "reachable" in serialized
    assert "health_message" in serialized


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


def test_openapi_llm_provider_endpoint_includes_examples():
    schema = app.openapi()

    provider_example = schema["components"]["schemas"]["LLMProviderCatalogResponse"]["example"]
    assert provider_example["default_provider_id"] == "auto"
    assert provider_example["providers"][1]["provider_id"] == "openai"
    assert provider_example["providers"][1]["reachable"] is True
    assert schema["paths"]["/llm/providers"]["get"]["tags"] == ["LLM"]


def test_env_example_lists_multi_provider_variables():
    env_example = Path(__file__).resolve().parents[2] / ".env.example"
    content = env_example.read_text(encoding="utf-8")

    assert "OPENAI_API_KEY=" in content
    assert "OPENROUTER_API_KEY=" in content
    assert "GROQ_API_KEY=" in content
    assert "TOGETHER_API_KEY=" in content
    assert "LOOPLAMP_ENABLE_OLLAMA=false" in content
    assert "OLLAMA_BASE_URL=http://host.docker.internal:11434/v1" in content
    assert "NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000" in content


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
    assert "tool_calls" in serialized
    assert "agent_loop" in serialized
    assert "inspection" in serialized
    assert "comparison" in serialized
    assert "evidence_summary" in serialized
    assert "control_themes" in serialized
    assert "obligations" in serialized
    assert "decision_basis" in serialized
    assert "recommended_controls" in serialized
    assert "follow_up_checks" in serialized
    assert "symptoms" in serialized
    assert "red_flags" in serialized
    assert "escalation_criteria" in serialized
    assert "care_constraints" in serialized
    assert "symptom_summary" in serialized
    assert "escalation_path" in serialized
    assert "patient_safety_notes" in serialized
    assert "transaction_signals" in serialized
    assert "customer_impact_checks" in serialized
    assert "fraud_indicators" in serialized
    assert "next_actions" in serialized
    assert "service_actions" in serialized
    assert "customer_message_points" in serialized
    assert "fraud_follow_ups" in serialized
    assert "fault_signals" in serialized
    assert "subsystem_risks" in serialized
    assert "repair_prerequisites" in serialized
    assert "safety_checks" in serialized
    assert "diagnosis_summary" in serialized
    assert "repair_plan" in serialized
    assert "vehicle_safety_notes" in serialized
    assert "defect_signals" in serialized
    assert "line_impact" in serialized
    assert "containment_actions" in serialized
    assert "restart_gates" in serialized
    assert "containment_summary" in serialized
    assert "production_actions" in serialized
    assert "quality_follow_ups" in serialized
    assert "order_signals" in serialized
    assert "policy_constraints" in serialized
    assert "fulfillment_risks" in serialized
    assert "customer_resolution_actions" in serialized
    assert "refund_basis" in serialized
    assert "resolution_plan" in serialized
    assert "inventory_notes" in serialized
    assert "graph_state_score" in serialized
    assert "graph_state_expected_fields" in serialized
    assert "graph_state_present_fields" in serialized
    assert "graph_state_missing_fields" in serialized
    assert "search_query" in serialized
    assert "agent_trace" in serialized
    assert "planned_query" in serialized
    assert "comparison_summary" in serialized
    assert "summary_digest" in serialized
    assert "added_sources" in serialized
    assert "steps" in serialized
