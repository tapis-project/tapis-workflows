class KubernetesImageBuilder:
    def build(self, build_context):
        print(build_context)

image_builder = KubernetesImageBuilder()