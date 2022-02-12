from typing import Union, List

from django.http import JsonResponse


class BaseResponse(JsonResponse):
    def __init__(self,
        status: int = 200,
        success: bool = True,
        message: str = "success",
        result: Union[dict, List[dict]] = None
    ):
        self.success = success
        self.status = status
        self.message = str(message)
        self.result = result
        JsonResponse.__init__(self, vars(self), status=status)