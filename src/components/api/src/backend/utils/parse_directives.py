import re

from backend.conf.constants import DIRECTIVE_DELIMITER, DIRECTIVE_SET_PATTERN, SUPPORTED_DIRECTIVES, DIRECTIVE_KEY_VAL_DELIMITER

def parse_directives(directive_string):
    # Parse the directive string from the commit message
    pattern = re.compile(DIRECTIVE_SET_PATTERN, re.UNICODE)
    matches = pattern.findall(directive_string)
    
    directives = None
    if len(matches) == 0:
        return directives

    directive_set_str = matches[0]

    directives = {}
    directive_set = directive_set_str.split(DIRECTIVE_DELIMITER)

    for directive_str in directive_set:
        # Catch the insances in which a pipe("|") exists with no key or key-value
        if directive_str == "":
            continue

        key_val = directive_str.split(DIRECTIVE_KEY_VAL_DELIMITER)
        key = key_val[0].upper()
        if key in SUPPORTED_DIRECTIVES:
            val = None if len(key_val) == 1 else key_val[1]
            directives[key] = val

    if len(directives) == 0:
        return None

    return directives
