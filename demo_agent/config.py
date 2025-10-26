# configuration for mcp agent demo

import os
from typing import Optional


class Config:
    """
    configuration management for demo agent
    
    loads settings from environment variables
    """
    
    def __init__(self):
        self.openai_api_key = self._get_openai_key()
        self.model = os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview")
        self.temperature = float(os.getenv("OPENAI_TEMPERATURE", "0.7"))
        self.max_tokens = int(os.getenv("OPENAI_MAX_TOKENS", "4096"))
        
        # mcp settings
        self.mcp_timeout = int(os.getenv("MCP_TIMEOUT", "30"))
        
        # ui settings
        self.theme = os.getenv("DEMO_THEME", "dark")
        
    def _get_openai_key(self) -> str:
        """get openai api key from environment"""
        key = os.getenv("OPENAI_API_KEY")
        
        if not key:
            raise ValueError(
                "OPENAI_API_KEY not set. please export it:\n"
                "export OPENAI_API_KEY='your-key-here'"
            )
        
        return key
    
    def validate(self):
        """validate configuration"""
        if not self.openai_api_key:
            raise ValueError("openai api key is required")
        
        if self.temperature < 0 or self.temperature > 2:
            raise ValueError("temperature must be between 0 and 2")
        
        return True

