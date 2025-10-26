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
    cursor_param = pagination_info.get("cursor_param")
    limit_param = pagination_info.get("limit_param")
    
    if not pagination_info.get("has_pagination"):
        return func(**kwargs)
    
    all_items = []
    page_count = 0
    max_pages = 10  # safety limit
    
    # set reasonable page size
    if limit_param and limit_param not in kwargs:
        kwargs[limit_param] = min(50, max_items)
    
    while len(all_items) < max_items and page_count < max_pages:
        try:
            result = func(**kwargs)
            page_count += 1
            
            # extract items from result
            items = _extract_items(result)
            if not items:
                break
            
            all_items.extend(items)
            
            # check for next page cursor
            next_cursor = _extract_next_cursor(result)
            if not next_cursor or not cursor_param:
                break
            
            # update cursor for next page
            kwargs[cursor_param] = next_cursor
            
        except Exception as e:
            # if pagination fails, return what we have
            break
    
    return {
        "items": all_items[:max_items],
        "count": len(all_items[:max_items]),
        "pages_collected": page_count,
        "truncated": len(all_items) > max_items
    }


def _extract_items(result):
    """extract items from various result formats."""
    if hasattr(result, "items"):
        items = result.items
        if callable(items):
            items = items()
        return list(items) if items else []
    elif hasattr(result, "data"):
        return list(result.data) if result.data else []
    elif isinstance(result, list):
        return result
    elif isinstance(result, dict) and "items" in result:
        return result["items"]
    return []


def _extract_next_cursor(result):
    """extract next page cursor from result."""
    if hasattr(result, "next_page_token"):
        return result.next_page_token
    elif hasattr(result, "next_cursor"):
        return result.next_cursor
    elif hasattr(result, "next"):
        return result.next
    elif isinstance(result, dict):
        return result.get("next_page_token") or result.get("next_cursor") or result.get("next")
    return None
