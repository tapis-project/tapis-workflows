def one_in(strings, target):
    for string in strings:
        if string in target:
            return True
    return False