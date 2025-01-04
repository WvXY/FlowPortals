from g_primitives import Vertex, Edge, Face


class _FInfo:
    def __init__(self):
        self.room = None
        self.is_visited = False
        self.is_active = True


class FVertex(Vertex, _FInfo):
    def __init__(self, xy):
        # Vertex.__init__(self, xy)
        # super()._FInfo.__init__(self)
        # _FInfo.__init__(self)
        super().__init__(xy)

    def __hash__(self):
        # for not hashable error
        return hash(self.guid)


class FEdge(Edge, _FInfo):
    def __init__(self, origin, to):
        Edge.__init__(self, origin, to)
        _FInfo.__init__(self)

    def disconnect(self):
        if self.is_visited:
            return False
        if self.is_blocked:
            return False

        super().disconnect()
        self.is_visited = True
        self.twin.is_visited = True
        return True


class FFace(Face, _FInfo):
    def __init__(self):
        Face.__init__(self)
        _FInfo.__init__(self)

    def merge(self, other: "FFace"):
        e = self.get_shared_edge(other)
        if e is None or e.is_visited:
            return False
        if e.is_blocked:
            return False

        e.disconnect()

        e.is_visited = True
        e.twin.is_visited = True
        return True


class FRoom(_FInfo):
    __room_list = []
    __rid = 0

    def __init__(self):
        _FInfo.__init__(self)
        FRoom.__room_list.append(self)
        self.rid = FRoom.__rid
        FRoom.__rid += 1

        self.faces = set()
        self.adjs = set()

    def add_adj(self, room):
        self.adjs.add(room)

    def get_all_edges(self):
        all_edges = set()
        for f in self.faces:
            all_edges.update(f.edges)
        return all_edges

    def get_wall_edges(self):
        all_edges = self.get_all_edges()
        wall_edges = set()
        for e in all_edges:
            if e.twin is None or e.twin not in all_edges:
                wall_edges.add(e)
        return wall_edges

    def get_area(self):
        return sum([f.area for f in self.faces])

    def get_center(self):
        centers = [f.center for f in self.faces]
        areas = [f.area for f in self.faces]
        area_sum = sum(areas)
        x = sum([c[0] * a for c, a in zip(centers, areas)]) / area_sum
        y = sum([c[1] * a for c, a in zip(centers, areas)]) / area_sum
        return (x, y)

    def get_shared_edge(self, other: "FRoom"):
        other_wall_edges = other.get_wall_edges()
        shared_edges = []
        for e in self.get_wall_edges():
            if e.twin in other_wall_edges:
                shared_edges += [e, e.twin]
        return shared_edges

    def get_by_rid(rid):
        return next((r for r in FRoom.__room_list if r.rid == rid), None)


# Alias
FNode = FVertex
FPoint = FVertex
