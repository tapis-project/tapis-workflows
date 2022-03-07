from celery import Celery

from conf.configs import BROKER_HOST, BROKER_PORT, BROKER_USER, BROKER_PASSWORD
from core.ActionDispatcher import action_dispatcher
from core.ActionResult import ActionResult
from errors.actions import InvalidActionTypeError


app = Celery(
    "tasks",
    broker=f"amqps://{BROKER_USER}:{BROKER_PASSWORD}@{BROKER_HOST}:{BROKER_PORT}/{BROKER_HOST}"
)

@app.task
def dispatch_action(action, pipeline_context, on_finish_callback):
    # Dispatch the action
    try:
        action_result = action_dispatcher.dispatch(action, pipeline_context)
    except InvalidActionTypeError as e:
        action_result = ActionResult(1, errors=[str(e)])
        
    print(action_result.__dict__) # TODO remove
    
    # Run the on_finish_callback
    on_finish_callback(action, action_result, pipeline_context)