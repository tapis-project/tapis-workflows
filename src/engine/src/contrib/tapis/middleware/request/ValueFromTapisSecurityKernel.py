from owe_python_sdk.middleware import RequestMiddleware


class ValueFromTapisSecurityKernal(RequestMiddleware):
    def __call__(self, request):
        for key, envvar_value in request.env.items():
            # Get the sk secret name
            sk_id = getattr(request.env.get(key).value_from, "tapis-security-kernel", None)
            
            if sk_id != None:
                # TODO get value from SK
                sk_secret_value = "TODOSecretValueFromSK"
                envvar_value.value = sk_secret_value
                setattr(request.env, key, envvar_value)

        return request