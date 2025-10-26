"""discover methods from python modules."""
import inspect
from safety import is_dangerous
from pagination import has_pagination


def discover_methods(module, module_name, allow_dangerous=False):
    """find all callable methods in a module."""
    methods = []
    
    # find functions
    for name, obj in inspect.getmembers(module, inspect.isfunction):
        if not name.startswith("_"):
            sig = _get_signature(obj)
            if sig:
                method_info = _create_method_info(
                    f"{module_name}.{name}", 
                    obj, 
                    sig,
                    allow_dangerous
                )
                if method_info:
                    methods.append(method_info)
    
    # find class methods
    for class_name, cls in inspect.getmembers(module, inspect.isclass):
        if not class_name.startswith("_"):
            for method_name, method in inspect.getmembers(cls, inspect.isfunction):
                if not method_name.startswith("_"):
                    sig = _get_signature(method)
                    if sig:
                        method_info = _create_method_info(
                            f"{module_name}.{class_name}.{method_name}",
                            method,
                            sig,
                            allow_dangerous
                        )
                        if method_info:
                            methods.append(method_info)
    
    return methods


def _get_signature(obj):
    """safely get signature."""
    try:
        return inspect.signature(obj)
    except:
        return None


def _create_method_info(name, obj, sig, allow_dangerous):
    """create method metadata."""
    dangerous = is_dangerous(name)
    
    # filter out dangerous methods unless explicitly allowed
    if dangerous and not allow_dangerous:
        return None
    
    return {
        "name": name,
        "callable": obj,
        "signature": sig,
        "docstring": inspect.getdoc(obj),
        "is_dangerous": dangerous,
        "has_pagination": has_pagination(sig)
    }
