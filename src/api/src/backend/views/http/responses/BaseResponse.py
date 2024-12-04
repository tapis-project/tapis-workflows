from typing import Union, List

from django.http import JsonResponse

from backend.conf.constants import API_VERSION


class BaseResponse(JsonResponse):
    def __init__(self,
        status: int = 200,
        success: bool = True,
        message: str = "Success",
        result: Union[dict, List[dict], str] = None,
        metadata: dict = {}
    ):
        # Conform to the tapis response object schema
        self.status = "success" if success else "error"
        self.message = str(message)
        self.result = result
        self.metadata = metadata
        self.version = API_VERSION

        # Set the metadata with some nice-to-have properties for api consumers
        self.metadata["success"] = success
 
        JsonResponse.__init__(self, vars(self), status=status)