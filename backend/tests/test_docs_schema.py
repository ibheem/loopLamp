from backend.core.models import QueryRequest


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
