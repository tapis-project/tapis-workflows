from backend.views.http.responses.BaseResponse import BaseResponse

class ResourceURLResponse(BaseResponse):
    def __init__(self, url: str, message: str=None):
        BaseResponse.__init__(
            self,
            status=201,
            success=True,
            message=message if message is not None else "created",
            result={"url": url}
        )

class NoContentResponse(BaseResponse):
    def __init__(self, message: str=None):
        BaseResponse.__init__(
            self,
            status=204,
            success=True,
            message=message if message is not None else "no content",
            result={}
        )
