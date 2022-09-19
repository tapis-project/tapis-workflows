from backend.conf.constants import (
    DJANGO_WORKFLOW_EXECUTOR_TOKEN_HEADER,
    WORKFLOW_EXECUTOR_ACCESS_TOKEN
)


def one_in(strings, target):
    for string in strings:
        if string in target:
            return True
    return False

def executor_request_is_valid(request):
    # Check that the X-WORKFLOW-EXECUTOR-TOKEN header is set
    if DJANGO_WORKFLOW_EXECUTOR_TOKEN_HEADER not in request.META:
        return False

    executor_token = request.META[DJANGO_WORKFLOW_EXECUTOR_TOKEN_HEADER]
    if executor_token != WORKFLOW_EXECUTOR_ACCESS_TOKEN:
        return False

    return True

    