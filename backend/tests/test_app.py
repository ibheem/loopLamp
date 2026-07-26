from backend.app.main import root


def test_root_endpoint():
    assert root() == {"message": "Agentic System Backend Ready"}
