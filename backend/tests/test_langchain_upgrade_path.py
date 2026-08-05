from backend.agents.langchain_domain_config import LANGCHAIN_AGENT_DOMAINS, prompt_guidance_for_domain, uses_langchain_create_agent
from backend.core.models import DomainInsight, DomainRecommendation, DomainReport
from backend.services import llm_provider as llm_provider_module
from backend.services.llm_provider import OpenAIResponsesReportProvider
from backend.tests.langchain_test_support import (
    FakeToolAwareProvider,
    build_langchain_report_agent_for_test,
    make_single_document,
)
from backend.workflows.query_graph import QueryGraphWorkflow
from backend.services.retrieval import RetrievalService


def test_langchain_domain_config_centralizes_supported_domains_and_guidance():
    assert uses_langchain_create_agent("telecom_security") is True
    assert uses_langchain_create_agent("manufacturing") is True
    assert uses_langchain_create_agent("general") is False
    assert "ecommerce" in LANGCHAIN_AGENT_DOMAINS
    assert "refund or policy constraints" in prompt_guidance_for_domain("ecommerce")
    assert prompt_guidance_for_domain("unknown_domain") == ""


def test_query_graph_uses_langgraph_backend_when_dependency_is_installed():
    workflow = QueryGraphWorkflow(RetrievalService())

    assert workflow.backend_name == "langgraph"


def test_langchain_provider_builds_chat_model_for_openai_compatible_stack():
    provider = FakeToolAwareProvider()

    model = provider.build_chat_model()

    assert model is not None
    assert provider.chat_models == ["gpt-5-mini"]


def test_langchain_provider_uses_structured_output_runtime(monkeypatch):
    class FakeStructuredRunnable:
        def invoke(self, prompt):
            assert "strictly grounded" in prompt
            return {"grounded": True, "summary": "Checked the evidence."}

    class FakeChatModel:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

        def with_structured_output(self, schema, method="json_schema"):
            assert method == "json_schema"
            assert schema["type"] == "object"
            return FakeStructuredRunnable()

    monkeypatch.setattr(llm_provider_module, "ChatOpenAI", FakeChatModel)
    provider = OpenAIResponsesReportProvider(
        api_key="test-key",
        model="gpt-5-mini",
        escalation_model="gpt-5-mini",
        provider_id="openai",
        requires_api_key=True,
    )

    payload = provider._run_json_schema_prompt(
        model_name="gpt-5-mini",
        prompt="Return strictly grounded evidence review.",
        schema_name="evidence_review",
        schema={
            "type": "object",
            "properties": {
                "grounded": {"type": "boolean"},
                "summary": {"type": "string"},
            },
            "required": ["grounded", "summary"],
        },
    )

    assert payload == '{"grounded": true, "summary": "Checked the evidence."}'


def test_langchain_create_agent_report_agent_returns_structured_report():
    agent, _provider = build_langchain_report_agent_for_test(
        "telecom_security",
        DomainReport(
            domain="telecom_security",
            summary="Based on the retrieved context, isolate the affected SS7 route and validate signaling controls.",
            insights=[
                DomainInsight(
                    title="Route containment is supported",
                    severity="high",
                    detail="The evidence points to immediate route isolation.",
                ),
                DomainInsight(
                    title="Control review follows containment",
                    severity="medium",
                    detail="The evidence also supports validating signaling controls after isolation.",
                ),
            ],
            recommendations=[
                DomainRecommendation(priority=1, action="Isolate the affected SS7 route."),
                DomainRecommendation(priority=2, action="Validate signaling firewall controls."),
            ],
        ),
        expected_tool_count=3,
    )
    documents = make_single_document(
        "SS7 anomaly triggered OTP failures. Isolate the affected route and validate signaling controls.",
        "test_data/telecom_incident.txt",
        file_type="text",
    )

    report = agent.generate_report_from_state(
        query="What action is recommended for the SS7 issue?",
        context_documents=documents,
    )
    metadata = agent.runtime_metadata()

    assert report.domain == "telecom_security"
    assert report.source_refs
    assert metadata["agent_loop"] == "langchain_create_agent"
    assert metadata["used_fallback"] == "false"
    assert metadata["provider_mode"] == "openai_agent"


def test_langchain_create_agent_financial_risk_report_agent_returns_structured_report():
    agent, _provider = build_langchain_report_agent_for_test(
        "financial_risk",
        DomainReport(
            domain="financial_risk",
            summary="Based on the retrieved context, validate delegated authority, preserve audit evidence, and confirm release approvals.",
            insights=[
                DomainInsight(
                    title="Delegated authority is material",
                    severity="high",
                    detail="The evidence shows release governance depends on approver authority.",
                ),
                DomainInsight(
                    title="Audit evidence must be retained",
                    severity="medium",
                    detail="The evidence points to documentary retention and traceability obligations.",
                ),
            ],
            recommendations=[
                DomainRecommendation(priority=1, action="Validate approver authority before release."),
                DomainRecommendation(priority=2, action="Preserve documentary audit trail for approvals."),
            ],
        ),
        expected_prompt_fragment="financial risk",
    )
    documents = make_single_document(
        "Delegated authority clauses require release approvals and documentary audit evidence.",
        "test_data/finance/policy.pdf",
        file_type="pdf",
    )

    report = agent.generate_report_from_state(
        query="What controls should be checked before funds are released?",
        context_documents=documents,
    )

    assert report.domain == "financial_risk"
    assert report.source_refs
    assert report.recommendations[0].action == "Validate approver authority before release."


def test_langchain_create_agent_medical_report_agent_returns_structured_report():
    agent, _provider = build_langchain_report_agent_for_test(
        "medical_qa",
        DomainReport(
            domain="medical_qa",
            summary="Based on the retrieved context, escalate persistent chest pain for urgent clinical assessment and review contraindications before medication guidance.",
            insights=[
                DomainInsight(
                    title="Persistent symptoms are a red flag",
                    severity="high",
                    detail="The evidence treats ongoing chest pain as escalation-worthy.",
                ),
                DomainInsight(
                    title="Contraindications must be reviewed",
                    severity="medium",
                    detail="The evidence supports checking medication constraints before applying care guidance.",
                ),
            ],
            recommendations=[
                DomainRecommendation(priority=1, action="Escalate for urgent clinical assessment."),
                DomainRecommendation(priority=2, action="Review contraindications before medication guidance."),
            ],
        ),
        expected_prompt_fragment="medical",
    )
    documents = make_single_document(
        "Persistent chest pain with worsening symptoms requires escalation and contraindication review.",
        "test_data/healthcare/clinical_guide.pdf",
        file_type="pdf",
    )

    report = agent.generate_report_from_state(
        query="What should be done for persistent chest pain?",
        context_documents=documents,
    )

    assert report.domain == "medical_qa"
    assert report.source_refs
    assert report.recommendations[0].action == "Escalate for urgent clinical assessment."


def test_langchain_create_agent_banking_report_agent_returns_structured_report():
    agent, _provider = build_langchain_report_agent_for_test(
        "banking_assistant",
        DomainReport(
            domain="banking_assistant",
            summary="Based on the retrieved context, capture the transaction reference, review the duplicate debit, and assess whether suspicious activity follow-up is required.",
            insights=[
                DomainInsight(
                    title="Duplicate debit is the primary signal",
                    severity="high",
                    detail="The evidence centers on transaction-reference handling for duplicate debit complaints.",
                ),
                DomainInsight(
                    title="Fraud review may be needed",
                    severity="medium",
                    detail="The evidence supports checking for suspicious repeat activity and authorization issues.",
                ),
            ],
            recommendations=[
                DomainRecommendation(priority=1, action="Capture the transaction reference and log the complaint."),
                DomainRecommendation(priority=2, action="Review whether suspicious activity escalation is required."),
            ],
        ),
        expected_prompt_fragment="banking",
    )
    documents = make_single_document(
        "Duplicate debit complaints require transaction reference capture and suspicious-activity review when usage looks unexpected.",
        "test_data/banking_assistant/atm_notice.txt",
    )

    report = agent.generate_report_from_state(
        query="What should be done for a duplicate debit complaint?",
        context_documents=documents,
    )

    assert report.domain == "banking_assistant"
    assert report.source_refs
    assert report.recommendations[0].action == "Capture the transaction reference and log the complaint."


def test_langchain_create_agent_ecommerce_report_agent_returns_structured_report():
    agent, _provider = build_langchain_report_agent_for_test(
        "ecommerce",
        DomainReport(
            domain="ecommerce",
            summary="Based on the retrieved context, validate refund eligibility against the return policy, confirm shipment status, and use stock-aware resolution steps.",
            insights=[
                DomainInsight(
                    title="Policy window drives refund eligibility",
                    severity="high",
                    detail="The evidence points to a policy-governed refund decision rather than immediate approval.",
                ),
                DomainInsight(
                    title="Replacement depends on fulfillment state",
                    severity="medium",
                    detail="The evidence supports checking shipment status and stock before promising an exchange.",
                ),
            ],
            recommendations=[
                DomainRecommendation(priority=1, action="Validate refund eligibility against the return policy."),
                DomainRecommendation(priority=2, action="Confirm shipment status and stock before offering replacement."),
            ],
        ),
        expected_prompt_fragment="ecommerce",
    )
    documents = make_single_document(
        "Delayed shipment refund requests require policy review, shipment confirmation, and stock-aware replacement handling.",
        "test_data/ecommerce/customer_issue.txt",
    )

    report = agent.generate_report_from_state(
        query="What should support do for a delayed-shipment refund request?",
        context_documents=documents,
    )

    assert report.domain == "ecommerce"
    assert report.source_refs
    assert report.recommendations[0].action == "Validate refund eligibility against the return policy."


def test_langchain_create_agent_automotive_report_agent_returns_structured_report():
    agent, _provider = build_langchain_report_agent_for_test(
        "automotive",
        DomainReport(
            domain="automotive",
            summary="Based on the retrieved context, confirm the DTC, inspect the brake subsystem, and complete safety checks before return to service.",
            insights=[
                DomainInsight(
                    title="Diagnostic confirmation comes first",
                    severity="high",
                    detail="The evidence supports validating the DTC before replacing parts.",
                ),
                DomainInsight(
                    title="Safety validation gates closure",
                    severity="medium",
                    detail="The evidence supports brake inspection and vehicle-safety confirmation before release.",
                ),
            ],
            recommendations=[
                DomainRecommendation(priority=1, action="Confirm the DTC before parts replacement."),
                DomainRecommendation(priority=2, action="Inspect the brake subsystem and verify safety before release."),
            ],
        ),
        expected_prompt_fragment="automotive",
    )
    documents = make_single_document(
        "DTC P0420 requires confirmation before replacement, and brake warnings require subsystem inspection plus safety validation before return to service.",
        "test_data/automotive/service_manual.txt",
    )

    report = agent.generate_report_from_state(
        query="What should be checked for a brake-related warning?",
        context_documents=documents,
    )

    assert report.domain == "automotive"
    assert report.source_refs
    assert report.recommendations[0].action == "Confirm the DTC before parts replacement."


def test_langchain_create_agent_manufacturing_report_agent_returns_structured_report():
    agent, _provider = build_langchain_report_agent_for_test(
        "manufacturing",
        DomainReport(
            domain="manufacturing",
            summary="Based on the retrieved context, isolate the affected lot, validate the SOP step, and hold restart until quality approval is documented.",
            insights=[
                DomainInsight(
                    title="Containment precedes restart",
                    severity="high",
                    detail="The evidence supports isolating the affected lot before any restart decision.",
                ),
                DomainInsight(
                    title="Quality approval gates recovery",
                    severity="medium",
                    detail="The evidence supports SOP validation and documented quality approval before resuming production.",
                ),
            ],
            recommendations=[
                DomainRecommendation(priority=1, action="Isolate the affected lot and assign corrective-action ownership."),
                DomainRecommendation(priority=2, action="Validate the SOP step and document quality approval before restart."),
            ],
        ),
        expected_prompt_fragment="manufacturing",
    )
    documents = make_single_document(
        "A quality defect requires lot isolation, corrective ownership, SOP validation, and documented quality approval before restart.",
        "test_data/manufacturing/quality_incident.txt",
    )

    report = agent.generate_report_from_state(
        query="What should happen after a quality defect is reported?",
        context_documents=documents,
    )

    assert report.domain == "manufacturing"
    assert report.source_refs
    assert report.recommendations[0].action == "Isolate the affected lot and assign corrective-action ownership."
