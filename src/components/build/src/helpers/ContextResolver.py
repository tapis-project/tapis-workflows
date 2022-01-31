from errors.context import ContextError


class ContextResolver:
    def __init__(self):
        self.is_visible = None

    def resolve(self, context, directives=[]):
        # Determine whether the context requires credentials to access
        self.is_visible = True if context.visibility == "public" else False
        self.directives = directives

        if context.type == "github":
            return self.github(context)
        elif context.type == "gitlab":
            return self.gitlab(context)
        else:
            raise ContextError(f"Unable to resolve context of type {context.type}")

    def github(self, context):
        extension = "git"
        domain_name = "github.com"
        scheme = "git://"

        cred_string = ""
        if self.is_visible == False:
            cred_string = f"{context.credential.data.token}@"

        return f"{scheme}{cred_string}{domain_name}/{context.repo}.{extension}"

    def gitlab(self, context):
        pass

context_resolver = ContextResolver()