"""allowlist and denylist filtering for tools."""
import fnmatch
import re


class ToolFilter:
    """filters tools based on allowlist/denylist patterns."""
    
    def __init__(self, allowlist=None, denylist=None):
        """
        initialize filter with patterns.
        
        patterns support:
        - exact matches: "kubernetes.CoreV1Api.list_pod"
        - wildcards: "kubernetes.*.list_*"
        - globs: "*.delete_*", "github.*"
        """
        self.allowlist = allowlist or []
        self.denylist = denylist or []
    
    def should_include(self, tool_name):
        """check if tool should be included."""
        # if allowlist specified, tool must match at least one pattern
        if self.allowlist:
            if not any(self._matches(tool_name, pattern) for pattern in self.allowlist):
                return False
        
        # if denylist specified, tool must not match any pattern
        if self.denylist:
            if any(self._matches(tool_name, pattern) for pattern in self.denylist):
                return False
        
        return True
    
    def _matches(self, tool_name, pattern):
        """check if tool name matches pattern."""
        # exact match
        if tool_name == pattern:
            return True
        
        # glob pattern
        if '*' in pattern or '?' in pattern:
            return fnmatch.fnmatch(tool_name, pattern)
        
        # prefix match
        if pattern.endswith('.*'):
            prefix = pattern[:-2]
            return tool_name.startswith(prefix + '.')
        
        return False
    
    def filter_tools(self, tools):
        """filter list of tools."""
        return [t for t in tools if self.should_include(t["name"])]


def parse_filter_patterns(pattern_string):
    """parse comma-separated filter patterns."""
    if not pattern_string:
        return []
    
    return [p.strip() for p in pattern_string.split(',') if p.strip()]

