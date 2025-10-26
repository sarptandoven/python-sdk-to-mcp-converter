"""configuration for mcp server."""
import os


class Config:
    """server configuration with full feature support."""
    
    def __init__(self):
        # basic settings
        self.sdks = self._load_sdks()
        # allow all operations by default to expose entire sdk functionality
        # requirement: "cover the entire space of what these SDKs are capable of"
        self.allow_dangerous = self._get_bool("ALLOW_DANGEROUS", True)
        self.redact_secrets = self._get_bool("REDACT_SECRETS", True)
        
        # filtering settings
        self.tool_allowlist = self._load_patterns("TOOL_ALLOWLIST")
        self.tool_denylist = self._load_patterns("TOOL_DENYLIST")
        
        # safety settings
        self.dry_run = self._get_bool("DRY_RUN", False)
        
        # execution settings
        self.max_retries = int(os.getenv("MAX_RETRIES", "3"))
        self.timeout_seconds = int(os.getenv("TIMEOUT", "30"))
        
        # pagination settings
        self.max_pagination_items = int(os.getenv("MAX_ITEMS", "100"))
        self.collect_all_pages = self._get_bool("COLLECT_ALL_PAGES", False)
        
        # llm settings
        self.use_llm = self._get_bool("USE_LLM", False)
        self.llm_model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
        
        # caching settings
        self.enable_cache = self._get_bool("ENABLE_CACHE", False)
        self.cache_ttl = int(os.getenv("CACHE_TTL", "300"))
        
        # rate limiting settings
        self.enable_rate_limit = self._get_bool("ENABLE_RATE_LIMIT", False)
        self.rate_limit_calls = int(os.getenv("RATE_LIMIT_CALLS", "100"))
        self.rate_limit_window = int(os.getenv("RATE_LIMIT_WINDOW", "60"))
        
        # logging settings
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
    
    def _load_sdks(self):
        """load sdk list from env."""
        sdk_str = os.getenv("SDKS", "os")
        return [s.strip() for s in sdk_str.split(",") if s.strip()]
    
    def _load_patterns(self, key):
        """load comma-separated patterns from env."""
        pattern_str = os.getenv(key, "")
        if not pattern_str:
            return []
        return [p.strip() for p in pattern_str.split(",") if p.strip()]
    
    def _get_bool(self, key, default):
        """get boolean from env."""
        value = os.getenv(key, str(default)).lower()
        return value in ["true", "1", "yes"]
    
    def __repr__(self):
        return (f"Config(sdks={self.sdks}, allow_dangerous={self.allow_dangerous}, "
                f"use_llm={self.use_llm}, cache={self.enable_cache}, "
                f"rate_limit={self.enable_rate_limit})")


def load_config():
    """load and validate configuration from environment."""
    config = Config()
    
    # validate llm settings
    if config.use_llm and not os.getenv("OPENAI_API_KEY"):
        print("warning: USE_LLM=true but OPENAI_API_KEY not set, disabling llm")
        config.use_llm = False
    
    # validate sdk list
    if not config.sdks:
        print("error: no sdks configured")
        config.sdks = ["os"]  # fallback
    
    return config
