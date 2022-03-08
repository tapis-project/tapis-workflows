class GraphValidator:
    def __init__(self):
        self.traversed_edges = []

    def has_cycle(self, action_dependency_map):
        self.action_dependency_map = action_dependency_map
        self.initial_actions = list(
            filter(lambda a: len(a.depends_on) == 0, self.action_dependency_map))

        for initial_action in self.initial_actions:
            return self.traverse(initial_action)


    def traverse(self, action_name):
        if action_name in self.visited:
            return True

        self.visited.append(action_name)
        
        dependencies = self.action_dependency_map[action_name]
        for dependency in dependencies:
            return self.has_cycle(dependency.name)

        self.visited = []

        return False

graph_validator = GraphValidator()