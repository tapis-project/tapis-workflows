from types import SimpleNamespace

from celery import Celery

from conf.configs import BROKER_URL, BACKEND_URL
from core.ActionDispatcher import action_dispatcher
from core.ActionResult import ActionResult
from errors.actions import InvalidActionTypeError


app = Celery(
    "tasks",
    broker=BROKER_URL,
    backend=BACKEND_URL,
    results_backend=BACKEND_URL
)

@app.task
def dispatch_action(action, pipeline_context):
    # Dispatch the action
    try:
        action_result = action_dispatcher.dispatch(
            SimpleNamespace(**action),
            SimpleNamespace(**pipeline_context)
        )
    except InvalidActionTypeError as e:
        action_result = ActionResult(1, errors=[str(e)])
        
    print(action_result.__dict__) # TODO remove