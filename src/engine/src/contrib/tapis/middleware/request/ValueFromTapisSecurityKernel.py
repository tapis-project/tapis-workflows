from owe_python_sdk.middleware import RequestMiddleware


class ValueFromTapisSecurityKernal(RequestMiddleware):
    def __call__(self, request):
        for key in dict(request.env):
            # Get the sk secret name
            envvar_value = getattr(request.env, key)
            sk_id = getattr(getattr(request.env, key).value_from, "tapis-security-kernel", None)
            
            if sk_id != None:
                # TODO get value from SK
                sk_secret_value = "TODOSecretValueFromSK"
                envvar_value.value = sk_secret_value
                setattr(request.env, key, envvar_value)

        return request