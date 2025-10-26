"""detect and handle pagination in sdk methods."""
import inspect


def has_pagination(signature):
    """check if method signature has pagination params."""
    params = signature.parameters
    param_names = [p.lower() for p in params.keys()]
    
    # common pagination parameter names
    pagination_params = ["page", "limit", "offset", "per_page", "cursor"]
    
    return any(p in param_names for p in pagination_params)


def get_pagination_info(signature):
    """extract pagination parameter info."""
    info = {}
    params = signature.parameters
    
    for name, param in params.items():
        name_lower = name.lower()
        if "page" in name_lower or "limit" in name_lower or "offset" in name_lower:
            info[name] = {
                "type": "pagination",
                "has_default": param.default != inspect.Parameter.empty
            }
    
    return info


def collect_paginated_results(func, kwargs, max_items=100):
    """try to collect paginated results."""
    # basic implementation
    # todo: handle different pagination styles
    
    results = []
    page = 1
    
    try:
        # attempt simple page-based collection
        while len(results) < max_items:
            if "page" in kwargs:
                kwargs["page"] = page
            
            result = func(**kwargs)
            
            # try to extract items
            if hasattr(result, "items"):
                items = result.items
            elif isinstance(result, list):
                items = result
            else:
                return result
            
            if not items:
                break
            
            results.extend(items)
            page += 1
            
            if len(items) < 10:  # probably last page
                break
    except:
        # fallback to single call
        return func(**kwargs)
    
    return results[:max_items]

