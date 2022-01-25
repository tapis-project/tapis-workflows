import re


DIRECTIVE_DELIMITER = "|"
SUPPORTED_DIRECTIVES = [
    "DEPLOY",
    "CUSTOM_TAG",
    "TAG_COMMIT_SHA",
    "DRY_RUN",
    "NO_PUSH",
]
DIRECTIVE_SET_PATTERN = r"(?<=[\[]{1})[a-zA-Z0-9\s:|._-]+(?=[\]]{1})"
KEY_VAL_DELIMITER = ":"

def parse_commit(commit_message):
    # Parse the directive string from the commit message
    pattern = re.compile(DIRECTIVE_SET_PATTERN, re.UNICODE)
    matches = pattern.findall(commit_message)
    
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

        key_val = directive_str.split(":")
        key = key_val[0].upper()
        if key in SUPPORTED_DIRECTIVES:
            val = None if len(key_val) == 1 else key_val[1]
            directives[key] = val

    if len(directives) == 0:
        return None

    return directives
