from builders.kaniko.Kaniko import builder as kaniko


class BuilderResolver():
    def resolve(self, build_method):
        if build_method == "kaniko":
            return kaniko
        else:
            raise Exception(f"Build method {build_method} is not a valid option")

builder_resolver = BuilderResolver()