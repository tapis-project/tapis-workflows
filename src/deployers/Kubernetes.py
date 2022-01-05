import subprocess

from configs import BASE_DIR

from deployers.BaseDeployer import BaseDeployer


class Kubernetes(BaseDeployer):
    def __init__(self):
        BaseDeployer.__init__(self)

    def handle(self, action_name, component_names):
        if len(component_names) == 0:
            component_names = [ component.spec.name for component in self.components ]

        components = self._get_components(component_names)

        action = getattr(self, action_name)

        for component in components:
            action(component.spec.resources)

    def burnup(self, resources):
        cmd_base = ["kubectl", "apply", "-f"]
        for resource in resources:
            if hasattr(resource, "onBurnup"):
                # TODO Do things on burnup
                pass
            cmd = cmd_base[:]
            cmd.append(BASE_DIR + resource.configPath)
            process = subprocess.run(
                cmd,
                stdout=subprocess.PIPE, 
                universal_newlines=True)

            print(process.stdout)

    def burndown(self, resources):
        cmd_base = ["kubectl", "delete", "-f"]
        for resource in resources:
            if hasattr(resource, "onBurndown") and resource.onBurndown == "delete":
                cmd = cmd_base[:]
                cmd.append(BASE_DIR + resource.configPath)
                process = subprocess.run(
                    cmd,
                    stdout=subprocess.PIPE, 
                    universal_newlines=True)

                print(process.stdout)
                

    def _get_components(self, component_names):
        valid_names = []
        components = []
        # Populate the components list with the components defined
        # in the component name list
        for component in self.components:
            # Populate the valid_names list with the names
            # of the components
            valid_names.append(component.spec.name)
            if component.spec.name in component_names:
                components.append(component)

        # Check that no invalid component names have been provided
        for name in component_names:
            if name not in valid_names:
                raise Exception(f"Component '{name}' is not defined in stack.json")

        return components
            

            

deployer = Kubernetes()