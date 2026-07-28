DOMAIN_CATALOG = {
    "telecom_security": {
        "label": "Telecom Security",
        "pattern": "rag_documents",
        "priority": 1,
        "status": "implemented",
        "sample_data": [
            "test_data/telecom_security/telecom_incident.txt",
            "test_data/telecom_security/threat_advisory.pdf",
            "test_data/telecom_security/ss7_logs.txt",
        ],
        "use_cases": [
            "incident report analysis",
            "log anomaly interpretation",
            "threat advisory summarization",
        ],
    },
    "financial_risk": {
        "label": "Financial Risk",
        "pattern": "rag_documents",
        "priority": 2,
        "status": "implemented",
        "sample_data": [
            "test_data/finance/FInal_GFR_upto_31_07_2024.pdf",
            "test_data/finance/master-circular.pdf",
            "test_data/finance/SEBI Booklet.pdf",
        ],
        "use_cases": [
            "clause retrieval",
            "compliance summarization",
            "risk guideline explanation",
        ],
    },
    "medical_qa": {
        "label": "Medical Q&A",
        "pattern": "rag_documents",
        "priority": 3,
        "status": "implemented",
        "sample_data": [
            "test_data/healthcare/GENERAL PRINCIPLES OF PHARMACOLOGY.pdf",
            "test_data/healthcare/Harrison_s Principles of Internal Medicine.pdf",
            "test_data/healthcare/HealthCareMagic-100k.json",
        ],
        "use_cases": [
            "clinical question answering",
            "patient query support",
            "medical concept explanation",
        ],
    },
    "banking_assistant": {
        "label": "Banking Assistant",
        "pattern": "rag_structured_hybrid",
        "priority": 4,
        "status": "planned",
        "sample_data": [
            "test_data/banking_assistant/transactions.csv",
            "test_data/banking_assistant/service_charges.pdf",
            "test_data/banking_assistant/atm_notice.txt",
        ],
        "use_cases": [
            "transaction insight generation",
            "policy retrieval",
            "service charge explanation",
        ],
    },
    "automotive": {
        "label": "Automotive",
        "pattern": "rag_structured_hybrid",
        "priority": 5,
        "status": "planned",
        "sample_data": [
            "test_data/automotive/service_manual.txt",
            "test_data/automotive/dtc_fault_codes.csv",
            "test_data/automotive/maintenance_bulletin.pdf",
        ],
        "use_cases": [
            "fault code interpretation",
            "service bulletin summarization",
            "maintenance action guidance",
        ],
    },
    "manufacturing": {
        "label": "Manufacturing",
        "pattern": "rag_structured_hybrid",
        "priority": 6,
        "status": "planned",
        "sample_data": [
            "test_data/manufacturing/production_log.csv",
            "test_data/manufacturing/sop_guidelines.pdf",
            "test_data/manufacturing/quality_incident.txt",
        ],
        "use_cases": [
            "process anomaly analysis",
            "root-cause support",
            "SOP retrieval",
        ],
    },
    "financial_sentiment": {
        "label": "Financial Sentiment",
        "pattern": "api_analytics_llm",
        "priority": 7,
        "status": "planned",
        "sample_data": [
            "test_data/financial_sentiment/news_sample.json",
            "test_data/financial_sentiment/stock_prices_sample.csv",
        ],
        "use_cases": [
            "headline sentiment scoring",
            "trend visualization",
            "impact analysis",
        ],
    },
    "sebi_regulatory": {
        "label": "SEBI Regulatory",
        "pattern": "rag_documents",
        "priority": 8,
        "status": "planned",
        "sample_data": [
            "test_data/sebi_regulatory/sebi_faq.pdf",
            "test_data/sebi_regulatory/circular_sample.pdf",
        ],
        "use_cases": [
            "regulatory question answering",
            "policy-change detection",
            "compliance risk extraction",
        ],
    },
}
