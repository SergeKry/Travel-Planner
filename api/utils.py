def deduplicate_list_preserve_order(items):
    """
    Remove duplicates from a list while preserving the original order.
    
    Args:
        items: List of items to deduplicate
        
    Returns:
        List with duplicates removed, preserving first occurrence order
    """
    seen = set()
    result = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result
