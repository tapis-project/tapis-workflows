def trunc_uuid(uuid):
    parts = str(uuid).split("-")
    return parts[0] + "..." + parts[-1]

def lbuffer_str(string, length=10):
    diff = length - len(string)

    if diff <= 0: return string
    
    buffer = " " * diff
    return buffer + string