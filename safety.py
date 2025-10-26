"""basic safety checks for method calls."""


# methods that look dangerous
DANGEROUS_PATTERNS = [
    "delete", "remove", "destroy", "drop",
    "create", "update", "patch", "write"
]


def is_dangerous(method_name):
    """check if method name looks dangerous."""
    name_lower = method_name.lower()
    return any(pattern in name_lower for pattern in DANGEROUS_PATTERNS)


def should_allow(method_name, allow_dangerous=False):
    """check if we should allow this method to run."""
    if not allow_dangerous and is_dangerous(method_name):
        return False
    return True


def redact_secrets(data):
    """try to remove secrets from data."""
    # basic redaction - needs work
    if isinstance(data, dict):
        redacted = {}
        for key, value in data.items():
            key_lower = key.lower()
            if any(word in key_lower for word in ["password", "token", "key", "secret"]):
                redacted[key] = "***"
            else:
                redacted[key] = redact_secrets(value)
        return redacted
    elif isinstance(data, list):
        return [redact_secrets(item) for item in data]
    return data

