"""discover methods from python modules."""
import inspect


def discover_methods(module, module_name):
    """find all callable methods in a module."""
    methods = []
    
    # find functions
    for name, obj in inspect.getmembers(module, inspect.isfunction):
        if not name.startswith("_"):
            methods.append({
                "name": f"{module_name}.{name}",
                "callable": obj,
                "signature": inspect.signature(obj)
            })
    
    # find class methods
    for class_name, cls in inspect.getmembers(module, inspect.isclass):
        if not class_name.startswith("_"):
            for method_name, method in inspect.getmembers(cls, inspect.isfunction):
                if not method_name.startswith("_"):
                    methods.append({
                        "name": f"{module_name}.{class_name}.{method_name}",
                        "callable": method,
                        "signature": inspect.signature(method)
                    })
    
    return methods

