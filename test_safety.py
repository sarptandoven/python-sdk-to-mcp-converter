"""tests for safety features."""
from safety import redact_secrets, should_allow


def test_redact_secrets():
    """test secret redaction."""
    data = {
        "username": "john",
        "password": "secret123",
        "api_key": "key_abc",
        "info": "public"
    }
    
    redacted = redact_secrets(data)
    
    assert redacted["username"] == "john"
    assert redacted["password"] == "***"
    assert redacted["api_key"] == "***"
    assert redacted["info"] == "public"


def test_should_allow():
    """test method allow logic."""
    assert should_allow("get_user", allow_dangerous=False) == True
    assert should_allow("delete_user", allow_dangerous=False) == False
    assert should_allow("delete_user", allow_dangerous=True) == True


if __name__ == "__main__":
    test_redact_secrets()
    test_should_allow()
    print("all tests passed")

