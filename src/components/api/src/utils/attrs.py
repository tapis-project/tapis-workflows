from webbrowser import get


def has_all_keys(obj, keys: list):
    for item in keys:
        if item not in obj:
            return False
    
    return True

def has_on_of_keys(obj, keys: list):
    for key in keys:
        if key in obj:
            return True
    
    return False
