"""pagination detection and handling."""
import inspect


CURSOR_PARAMS = ["page", "offset", "cursor", "next_token", "starting_after", "marker"]
LIMIT_PARAMS = ["limit", "per_page", "page_size", "max_results", "count", "top"]


def detect_pagination(signature):
    """detect pagination parameters in signature."""
    params = signature.parameters
    param_names = [p.lower() for p in params.keys()]
    
    cursor_param = None
    limit_param = None
    
    for name in params.keys():
        name_lower = name.lower()
        if not cursor_param and any(c in name_lower for c in CURSOR_PARAMS):
            cursor_param = name
        if not limit_param and any(l in name_lower for l in LIMIT_PARAMS):
            limit_param = name
    
    return {
        "has_pagination": cursor_param is not None or limit_param is not None,
        "cursor_param": cursor_param,
        "limit_param": limit_param
    }


def handle_paginated_call(func, kwargs, pagination_info, max_items=100):
    """handle paginated api calls."""
    if not pagination_info.get("has_pagination"):
        return func(**kwargs)
    
    # set reasonable limit if not specified
    limit_param = pagination_info.get("limit_param")
    if limit_param and limit_param not in kwargs:
        kwargs[limit_param] = min(max_items, 50)
    
    try:
        result = func(**kwargs)
        
        # try to extract items from common response formats
        if hasattr(result, "items"):
            items = result.items[:max_items]
            return {
                "items": items,
                "count": len(items),
                "truncated": len(result.items) > max_items
            }
        elif hasattr(result, "data"):
            data = result.data[:max_items]
            return {
                "items": data,
                "count": len(data),
                "truncated": len(result.data) > max_items
            }
        elif isinstance(result, list):
            return {
                "items": result[:max_items],
                "count": len(result[:max_items]),
                "truncated": len(result) > max_items
            }
        
        return result
    except Exception as e:
        # fallback to regular call
        return func(**kwargs)


def collect_all_pages(func, kwargs, pagination_info, max_items=100):
    """collect results from all pages."""
    # todo: implement proper multi-page collection
    # for now, just return single page
    return handle_paginated_call(func, kwargs, pagination_info, max_items)
