from errors.context import ContextError


class ContextResolver:
    def __init__(self):
        self.is_visible = None
        self.credential_accessor = "token"

    def resolve(self, context, directives=[]):
        # Determine whether the context requires credentials to access
        self.is_visible = True if context.visibility == "public" else False
        self.directives = directives

        if context.type == "github":
            self.credential_accessor = "personal_access_token"
            return self._github(context)
        elif context.type == "gitlab":
            self.credential_accessor = "token"
            return self._gitlab(context)
        else:
            raise ContextError(f"Unable to resolve context of type {context.type}")

    def _github(self, context, commit=None):
        extension = "git"
        domain_name = "github.com"
        scheme = "git://"

        cred_string = self._get_cred_string(context)

        # Resolve the branch string
        branch_string = ""
        if context.branch is not None:
            branch_string = f"#refs/heads/{context.branch}"

        # Resolve commit string
        commit_string = ""
        if commit is not None:
            commit_string = f"#{commit}"

        return f"{scheme}{cred_string}{domain_name}/{context.url}.{extension}{branch_string}{commit_string}"

    def _gitlab(self, context, commit=None):
        pass

    def _get_cred_string(self, context):
        # Return empty string if context repo is visible
        if self.is_visible: return ""

        identity = getattr(context, "identity", None)
        if identity != None:
            return f"{context.identity.credentials.data[self.credential_accessor]}@"
        
        
        return f"{context.credentials.data[self.credential_accessor]}@"
        


context_resolver = ContextResolver()
