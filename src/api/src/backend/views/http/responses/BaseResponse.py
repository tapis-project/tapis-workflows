from typing import Union, List

from django.http import JsonResponse

from backend.conf.constants import API_VERSION


class BaseResponse(JsonResponse):
    def __init__(self,
        status: int = 200,
        success: bool = True,
        message: str = "Success",
        result: Union[dict, List[dict]] = None,
        metadata: dict = {}
    ):
        self.status = status
        self.message = str(message)
        self.result = result
        self.metadata = metadata

        # Set the metadata with some nice-to-have properties for api consumers
        metadata["success"] = success
        metadata["http_status_code"] = status

        # Conform to the tapis response object schema
        tapis_status = "success" if success else "error"

        JsonResponse.__init__(self, vars(self), status=tapis_status, verion=API_VERSION)