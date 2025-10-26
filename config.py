"""configuration for mcp server."""
import os


class Config:
    """server configuration."""
    
    def __init__(self):
        self.sdks = self._load_sdks()
        self.allow_dangerous = self._get_bool("ALLOW_DANGEROUS", False)
        self.max_pagination_items = int(os.getenv("MAX_ITEMS", "100"))
        self.redact_secrets = self._get_bool("REDACT_SECRETS", True)
    
    def _load_sdks(self):
        """load sdk list from env."""
        sdk_str = os.getenv("SDKS", "os")
        return [s.strip() for s in sdk_str.split(",")]
    
    def _get_bool(self, key, default):
        """get boolean from env."""
        value = os.getenv(key, str(default)).lower()
        return value in ["true", "1", "yes"]
    
    def __repr__(self):
        return f"Config(sdks={self.sdks}, allow_dangerous={self.allow_dangerous})"


def load_config():
    """load configuration."""
    return Config()

