from django.forms.models import model_to_dict

from backend.views.http.responses.BaseResponse import BaseResponse

class ModelResponse(BaseResponse):
    def __init__(self, model, message=None):
        BaseResponse.__init__(
            self,
            status=200,
            success=True,
            message=message if message is not None else "success",
            result=model_to_dict(model)
        )


class ModelListResponse(BaseResponse):
    def __init__(self, query_set, message=None):
        models = []
        for model in query_set:
            models.append(model_to_dict(model))

        BaseResponse.__init__(
            self,
            message=message if message is not None else "success",
            result=models
        )

class ModelResponseOr404(BaseResponse):
    def __init__(self, model, message=None):
        if model is None:
            BaseResponse.__init__(
                self,
                status=404,
                success=False,
                message=message if message is not None else "Not Found"
            )
        else:
            BaseResponse.__init__(
                self,
                message=message if message is not None else "success",
                result=model_to_dict(model)
            )

