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

    def github(self, context, commit=None):
        extension = "git"
        domain_name = "github.com"
        scheme = "git://"

        cred_string = ""
        if self.is_visible == False:
            cred_string = f"{context.credential.data.token}@"

        # Resolve the branch string
        branch_string = ""
        if context.branch is not None:
            branch_string = f"#refs/heads/{context.branch}"

        # Resolve commit string
        commit_string = ""
        if commit is not None:
            commit_string = f"#{commit}"


        return f"{scheme}{cred_string}{domain_name}/{context.repo}.{extension}{branch_string}{commit_string}"

    def gitlab(self, context):
        pass

context_resolver = ContextResolver()