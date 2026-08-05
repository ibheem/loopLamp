LANGCHAIN_AGENT_DOMAINS = (
    "telecom_security",
    "financial_risk",
    "medical_qa",
    "banking_assistant",
    "ecommerce",
    "automotive",
    "manufacturing",
)

LANGCHAIN_DOMAIN_PROMPT_GUIDANCE = {
    "telecom_security": (
        "Prioritize grounded containment actions, signaling risk interpretation, and operationally safe "
        "follow-up controls.\n"
    ),
    "financial_risk": (
        "Prioritize governance controls, delegated authority, auditability, obligations, and decision-ready "
        "compliance actions.\n"
    ),
    "medical_qa": (
        "Prioritize clinically grounded symptom interpretation, red-flag escalation, contraindication awareness, "
        "and cautious patient-safety-oriented next steps.\n"
    ),
    "banking_assistant": (
        "Prioritize transaction signals, customer impact checks, fraud awareness, service-safe next actions, "
        "and policy-grounded customer communication.\n"
    ),
    "ecommerce": (
        "Prioritize order signals, refund or policy constraints, fulfillment clarity, inventory-aware actions, "
        "and customer-safe resolution steps.\n"
    ),
    "automotive": (
        "Prioritize fault signals, subsystem risks, repair prerequisites, vehicle safety checks, and "
        "technician-ready diagnostic actions.\n"
    ),
    "manufacturing": (
        "Prioritize defect signals, line impact, containment actions, restart gates, and production-safe "
        "quality follow-up actions.\n"
    ),
}


def uses_langchain_create_agent(domain: str) -> bool:
    return domain in LANGCHAIN_AGENT_DOMAINS


def prompt_guidance_for_domain(domain: str) -> str:
    return LANGCHAIN_DOMAIN_PROMPT_GUIDANCE.get(domain, "")
