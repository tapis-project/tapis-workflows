class GetSecretFromSecurityKernel:
    def __call__(self, payload, ctx):
        secret_name = payload.get("secret_name")
        secret_type = payload.get("secret_type")
        version = payload.version("version", 0)

        if secret_name and secret_type:
            raise Exception("Operation 'get_secret_from_sk' requires both 'secret_name' and 'secret_type' properties to be non-null")


        return request