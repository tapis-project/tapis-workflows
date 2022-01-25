def has_one_of(obj, attrs):
    for attribute in attrs:
        if hasattr(obj, attribute):
            return True

    return False
    