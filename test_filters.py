"""tests for tool filtering."""
from filters import ToolFilter, parse_filter_patterns


def test_allowlist():
    """test allowlist filtering."""
    filter = ToolFilter(allowlist=["os.*", "kubernetes.*.list_*"])
    
    assert filter.should_include("os.getcwd") == True
    assert filter.should_include("os.path.join") == True
    assert filter.should_include("kubernetes.CoreV1Api.list_pod") == True
    assert filter.should_include("github.Repository.create") == False


def test_denylist():
    """test denylist filtering."""
    filter = ToolFilter(denylist=["*.delete_*", "*.remove*"])
    
    assert filter.should_include("os.getcwd") == True
    assert filter.should_include("kubernetes.CoreV1Api.list_pod") == True
    assert filter.should_include("kubernetes.CoreV1Api.delete_pod") == False
    assert filter.should_include("github.Repository.remove") == False


def test_combined_filters():
    """test allowlist and denylist together."""
    filter = ToolFilter(
        allowlist=["kubernetes.*"],
        denylist=["*.delete_*"]
    )
    
    assert filter.should_include("kubernetes.CoreV1Api.list_pod") == True
    assert filter.should_include("kubernetes.CoreV1Api.delete_pod") == False
    assert filter.should_include("os.getcwd") == False


def test_exact_match():
    """test exact pattern matching."""
    filter = ToolFilter(allowlist=["os.getcwd"])
    
    assert filter.should_include("os.getcwd") == True
    assert filter.should_include("os.getcwdb") == False


def test_parse_patterns():
    """test pattern parsing."""
    patterns = parse_filter_patterns("os.*, kubernetes.*, github.*")
    assert len(patterns) == 3
    assert "os.*" in patterns
    
    empty = parse_filter_patterns("")
    assert len(empty) == 0


def test_filter_tools():
    """test filtering tool list."""
    tools = [
        {"name": "os.getcwd"},
        {"name": "os.remove"},
        {"name": "kubernetes.CoreV1Api.list_pod"},
        {"name": "kubernetes.CoreV1Api.delete_pod"}
    ]
    
    filter = ToolFilter(
        allowlist=["os.*", "kubernetes.*"],
        denylist=["*.delete_*", "*.remove*"]
    )
    
    filtered = filter.filter_tools(tools)
    assert len(filtered) == 2
    assert filtered[0]["name"] == "os.getcwd"
    assert filtered[1]["name"] == "kubernetes.CoreV1Api.list_pod"


if __name__ == "__main__":
    test_allowlist()
    test_denylist()
    test_combined_filters()
    test_exact_match()
    test_parse_patterns()
    test_filter_tools()
    print("all filter tests passed")

