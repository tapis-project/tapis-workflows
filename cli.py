import sys, subprocess, os

# Args passed from the command line
args = sys.argv[1:]
if len(args) < 2:
    args.append("--all")

# A list of services to validate the args against
valid_services = ["api", "mysql", "pipelines", "rabbitmq"]

# Buildable services
buildable_services = [ "api", "pipelines" ]

# Startable service
startable_services = [ "dashboard", "rabbitmq", "api" ]

# The action provided must correspond on of available functions
action = args[0]

# List of services upon which the action will be taken
services = args[1:]

def _validate(services):
    for service in services:
        if service not in valid_services:
            print(f"{service} is not a valid service")
            sys.exit(1)

def _startable_validate(services):
    for service in services:
        if service not in startable_services:
            print(f"{service} is not a startable service")
            sys.exit(1)

def start(services):
    _startable_validate(services)
    for service in services:
        if service == "dashboard":
            os.system("minikube dashboard")
        elif service == "rabbitmq":
            os.system("minikube service workflows-rabbitmq-service")
        elif service == "api":
            os.system("minikube service --url workflows-api-service")

# Burndown services
def down(services):
    _validate(services)
    if len(services) == 0:
        subprocess.run("./burndown")
        return

    for service in services:
        subprocess.run(f"./src/{service}/deploy/local/minikube/burndown")

# Burnup services
def up(services):
    _validate(services)
    if len(services) == 0:
        subprocess.run("./burnup")
        return

    for service in services:
        subprocess.run(f"./src/{service}/deploy/local/minikube/burnup")

# Burndown then burnup services
def restart(services):
    if "--all" in services:
        subprocess.run("./burndown")
        subprocess.run("./burnup")
        return
        
    down(services)
    up(services)

def build(services):
    down(services)
    for service in services:
        if service in buildable_services:
            os.system(f"docker build -t tapis/workflows-{service}:dev -f src/{service}/src/Dockerfile .")
    
    up(services)

# Burndown, build, push, then burnup services
def rebuild(services):
    down(services)
    for service in services:
        if service in buildable_services:
            os.system(f"docker build -t tapis/workflows-{service}:dev -f ./src/{service}/src/Dockerfile . && docker push tapis/workflows-{service}:dev")
    
    up(services)

def exec(services):
    if len(services) > 1:
        print("You can only watch one service at a time")

    service = services[0]

    print(f"Exec(ing) into {service}")
    os.system(f"service=\"$(kubectl get pods --no-headers -o custom-columns=':metadata.name' | grep {service}-deployment)\" && kubectl exec --stdin --tty $service -- /bin/bash")

def watch(services):
    if len(services) > 1:
        print("You can only watch one service at a time")

    service = services[0]

    print(f"Watching pod logs for the {service} deployment")
    os.system(f"service=\"$(kubectl get pods --no-headers -o custom-columns=':metadata.name' | grep {service}-deployment)\" && kubectl logs -f $service")

def clean(*args):
    args = args[0]
    if "images" in args:
        print("Removing dangling docker images")
        os.system("docker rmi $(docker images -qa -f 'dangling=true')")

    if "cache" in args:
        print("Deleting docker build cache")
        os.system("docker builder prune -a")

# Run action
if hasattr(sys.modules[__name__], action):
    getattr(sys.modules[__name__], action)(services)
    sys.exit(0)

# Exit if action not valid
print(f"{action} is not a valid action")
sys.exit(1)

