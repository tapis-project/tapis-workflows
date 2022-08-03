class GraphValidator:
    def __init__(self):
        self.last_task = None
        self.traversed_edges = []

    def has_cycle(self, task_dependency_map, initial_tasks):
        self.task_dependency_map = task_dependency_map
        initial_task_ids = [initial_task.id for initial_task in initial_tasks]

        for id in initial_task_ids:
            if len(self.task_dependency_map[id]) > 0:
                has_cycle = self.traverse(self.task_dependency_map[id][0], id)
                if has_cycle:
                    return True

            # self.traversed_edges = [] # TODO reset traversed edges here?

        return False

    def traverse(self, to_vertex, from_vertex):
        edge = f"{from_vertex}:{to_vertex}"
        if edge in self.traversed_edges:
            return True

        self.traversed_edges.append(edge)

        dependencies = self.task_dependency_map[to_vertex]
        for dependency in dependencies:
            has_cycle = self.traverse(dependency, to_vertex)
            if has_cycle:
                return True

        # self.traversed_edges = [] # TODO reset traversed edges here?

        return False
