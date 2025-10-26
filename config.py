"""configuration for mcp server."""
import os


class Config:
    """server configuration."""
    
    def __init__(self):
        self.sdks = self._load_sdks()
        self.allow_dangerous = self._get_bool("ALLOW_DANGEROUS", False)
        self.max_pagination_items = int(os.getenv("MAX_ITEMS", "100"))
        self.redact_secrets = self._get_bool("REDACT_SECRETS", True)
        self.use_llm = self._get_bool("USE_LLM", False)
        self.max_retries = int(os.getenv("MAX_RETRIES", "3"))
        self.timeout_seconds = int(os.getenv("TIMEOUT", "30"))
    
    def _load_sdks(self):
        """load sdk list from env."""
        sdk_str = os.getenv("SDKS", "os")
        return [s.strip() for s in sdk_str.split(",") if s.strip()]
    
    def _get_bool(self, key, default):
        """get boolean from env."""
        value = os.getenv(key, str(default)).lower()
        return value in ["true", "1", "yes"]
    
    def __repr__(self):
        return (f"Config(sdks={self.sdks}, allow_dangerous={self.allow_dangerous}, "
                f"use_llm={self.use_llm}, max_retries={self.max_retries})")


def load_config():
    """load configuration from environment."""
    config = Config()
    
    # validate openai key if llm is enabled
    if config.use_llm and not os.getenv("OPENAI_API_KEY"):
        print("warning: USE_LLM=true but OPENAI_API_KEY not set")
        config.use_llm = False
    
    return config
