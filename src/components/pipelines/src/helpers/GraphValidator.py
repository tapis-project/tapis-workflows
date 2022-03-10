class GraphValidator:
    def __init__(self):
        self.last_action = None
        self.traversed_edges = []

    def has_cycle(self, action_dependency_map, initial_actions):
        self.action_dependency_map = action_dependency_map
        initial_action_names = [ initial_action.name for initial_action in initial_actions ]

        for name in initial_action_names:
            has_cycle = self.traverse(self.action_dependency_map[name][0], name)
            if has_cycle:
                return True

            # self.traversed_edges = [] # TODO reset traversed edges here?

        return False

    def traverse(self, to_vertex, from_vertex):
        edge = f"{from_vertex}:{to_vertex}"
        if edge in self.traversed_edges:
            return True

        self.traversed_edges.append(edge)
        
        dependencies = self.action_dependency_map[to_vertex]
        for dependency in dependencies:
            has_cycle = self.traverse(dependency, to_vertex)
            if has_cycle:
                return True

        # self.traversed_edges = [] # TODO reset traversed edges here?

        return False