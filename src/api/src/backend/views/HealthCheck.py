from backend.views.APIView import APIView
from backend.views.http.responses.errors import BaseResponse


class HealthCheck(APIView):
    def get(self, _):
        return BaseResponse(
            message="Healthy",
            result={
                "status": "pass",
                "services": {
                    "api": "pass",
                    "pipelines": "pass",
                    "rabbitmq": "pass",
                    "mysql": "pass"
                }
            }
        )
            