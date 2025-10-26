"""basic tests for reflection."""
from reflection import discover_methods
from safety import is_dangerous
import types


def test_discovers_functions():
    """check that we can find functions."""
    module = types.ModuleType("test_module")
    
    def sample_func():
        return "test"
    
    module.sample_func = sample_func
    
    methods = discover_methods(module, "test_module")
    assert len(methods) > 0
    assert any(m["name"] == "test_module.sample_func" for m in methods)


def test_filters_dangerous_methods():
    """check that dangerous methods are filtered."""
    module = types.ModuleType("test_module")
    
    def safe_get():
        return "safe"
    
    def dangerous_delete():
        return "danger"
    
    module.safe_get = safe_get
    module.dangerous_delete = dangerous_delete
    
    methods = discover_methods(module, "test_module", allow_dangerous=False)
    names = [m["name"] for m in methods]
    
    assert "test_module.safe_get" in names
    assert "test_module.dangerous_delete" not in names


def test_dangerous_detection():
    """test dangerous method detection."""
    assert is_dangerous("delete_user") == True
    assert is_dangerous("get_user") == False
    assert is_dangerous("update_profile") == True
    assert is_dangerous("list_items") == False


if __name__ == "__main__":
    test_discovers_functions()
    test_filters_dangerous_methods()
    test_dangerous_detection()
    print("all tests passed")

