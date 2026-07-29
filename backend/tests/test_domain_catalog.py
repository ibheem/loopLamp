from backend.core.domain_catalog import DOMAIN_CATALOG


def test_domain_catalog_includes_required_domains():
    required_domains = {
        "telecom_security",
        "financial_risk",
        "medical_qa",
        "banking_assistant",
        "automotive",
        "manufacturing",
        "ecommerce",
        "financial_sentiment",
        "sebi_regulatory",
    }

    assert required_domains.issubset(DOMAIN_CATALOG.keys())


def test_domain_catalog_marks_automotive_and_manufacturing_as_implemented():
    assert DOMAIN_CATALOG["automotive"]["status"] == "implemented"
    assert DOMAIN_CATALOG["manufacturing"]["status"] == "implemented"
    assert DOMAIN_CATALOG["automotive"]["pattern"] == "rag_structured_hybrid"
    assert DOMAIN_CATALOG["manufacturing"]["pattern"] == "rag_structured_hybrid"


def test_domain_catalog_marks_financial_risk_as_implemented():
    assert DOMAIN_CATALOG["financial_risk"]["status"] == "implemented"
    assert any("test_data/finance/" in item for item in DOMAIN_CATALOG["financial_risk"]["sample_data"])


def test_domain_catalog_marks_medical_qa_as_implemented():
    assert DOMAIN_CATALOG["medical_qa"]["status"] == "implemented"
    assert any("test_data/healthcare/" in item for item in DOMAIN_CATALOG["medical_qa"]["sample_data"])


def test_domain_catalog_marks_banking_assistant_as_implemented():
    assert DOMAIN_CATALOG["banking_assistant"]["status"] == "implemented"
    assert any("test_data/banking_assistant/" in item for item in DOMAIN_CATALOG["banking_assistant"]["sample_data"])


def test_domain_catalog_marks_automotive_as_implemented():
    assert DOMAIN_CATALOG["automotive"]["status"] == "implemented"
    assert any("test_data/automotive/" in item for item in DOMAIN_CATALOG["automotive"]["sample_data"])


def test_domain_catalog_marks_manufacturing_as_implemented():
    assert DOMAIN_CATALOG["manufacturing"]["status"] == "implemented"
    assert any("test_data/manufacturing/" in item for item in DOMAIN_CATALOG["manufacturing"]["sample_data"])


def test_domain_catalog_marks_ecommerce_as_implemented():
    assert DOMAIN_CATALOG["ecommerce"]["status"] == "implemented"
    assert any("test_data/ecommerce/" in item for item in DOMAIN_CATALOG["ecommerce"]["sample_data"])
