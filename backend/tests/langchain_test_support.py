from backend.agents.langchain_report_agent import LangChainCreateAgentReportAgent
from backend.core.documents import Document
from backend.core.models import DomainReport
from backend.services.llm_provider import OpenAIResponsesReportProvider


class FakeCompiledAgent:
    def __init__(self, payload):
        self.payload = payload

    def invoke(self, _input):
        return self.payload


class FakeToolAwareProvider(OpenAIResponsesReportProvider):
    def __init__(self):
        super().__init__(
            api_key="test-key",
            model="gpt-5-mini",
            escalation_model="gpt-5-mini",
            provider_id="openai",
            requires_api_key=True,
        )
        self.chat_models = []

    def build_chat_model(self, model_override=None):
        selected_model = model_override or self.model
        self.chat_models.append(selected_model)
        return object()


def make_fake_agent_factory(
    report: DomainReport,
    *,
    expected_prompt_fragment: str | None = None,
    expected_tool_count: int | None = None,
):
    def fake_agent_factory(**kwargs):
        assert kwargs["response_format"] is DomainReport
        if expected_prompt_fragment:
            assert expected_prompt_fragment.lower() in kwargs["system_prompt"].lower()
        if expected_tool_count is not None:
            assert len(kwargs["tools"]) == expected_tool_count
        return FakeCompiledAgent(
            {
                "structured_response": report,
                "messages": [],
            }
        )

    return fake_agent_factory


def build_langchain_report_agent_for_test(
    domain_name: str,
    report: DomainReport,
    *,
    expected_prompt_fragment: str | None = None,
    expected_tool_count: int | None = None,
    provider: FakeToolAwareProvider | None = None,
):
    active_provider = provider or FakeToolAwareProvider()
    agent = LangChainCreateAgentReportAgent(
        provider=active_provider,
        domain_name=domain_name,
        agent_factory=make_fake_agent_factory(
            report,
            expected_prompt_fragment=expected_prompt_fragment,
            expected_tool_count=expected_tool_count,
        ),
    )
    return agent, active_provider


def make_single_document(content: str, source: str, *, chunk_index: int = 0, file_type: str = "txt"):
    return [
        Document(
            page_content=content,
            metadata={"source": source, "chunk_index": chunk_index, "file_type": file_type},
        )
    ]
