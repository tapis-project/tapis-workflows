import sys

from deployers.Kubernetes import deployer


args = sys.argv[1:]

if len(args) == 0:
    print("No arguments provided")
    sys.exit(1)

action = args[0]

if hasattr(deployer, action) == False:
    print(f"Deployer has no method {action}")
    sys.exit(1)

components = []
if len(args) > 1:
    components = args[1:]

deployer.handle(action, components)