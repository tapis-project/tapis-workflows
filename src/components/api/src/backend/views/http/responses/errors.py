from backend.views.http.responses.BaseResponse import BaseResponse

# 400
class BadRequest(BaseResponse):
    def __init__(self, message=None):
        BaseResponse.__init__(
            self,
            status=400,
            success=False,
            message=message if message is not None else "Bad Request"
        )

# 401
class Unauthorized(BaseResponse):
    def __init__(self, message=None):
        BaseResponse.__init__(
            self,
            status=401,
            success=False,
            message=message if message is not None else "Unauthorized"
        )

# 403
class Forbidden(BaseResponse):
    def __init__(self, message=None):
        BaseResponse.__init__(
            self,
            status=403,
            success=False,
            message=message if message is not None else "Forbidden"
        )

# 404
class NotFound(BaseResponse):
    def __init__(self, message=None):
        BaseResponse.__init__(
            self,
            status=404,
            success=False,
            message=message if message is not None else "Not Found"
        )

# 405
class MethodNotAllowed(BaseResponse):
    def __init__(self, message=None):
        BaseResponse.__init__(
            self,
            status=405,
            success=False,
            message=message if message is not None else "Method not allowed"
        )

# 409
class Conflict(BaseResponse):
    def __init__(self, message=None):
        BaseResponse.__init__(
            self,
            status=409,
            success=False,
            message=message if message is not None else "Conflict"
        )

# 415
class UnsupportedMediaType(BaseResponse):
    def __init__(self, message=None):
        BaseResponse.__init__(
            self,
            status=415,
            success=False,
            message=message if message is not None else "Unsupported media type",
        )

# 422
class UnprocessableEntity(BaseResponse):
    def __init__(self, message=None):
        BaseResponse.__init__(
            self,
            status=422,
            success=False,
            message=message if message is not None else "Unprocessable entity",
        )

# 500
class ServerError(BaseResponse):
    def __init__(self, message=None):
        BaseResponse.__init__(
            self,
            status=500,
            success=False,
            message=message if message is not None else "Server Error"
        )
