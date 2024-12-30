from u_geometry import closet_position_on_edge, del_vertex, add_vertex
from f_primitives import FPoint, FEdge, FFace

import numpy as np
from copy import deepcopy, copy


class FDoor:
    def __init__(self, edge, fp=None):
        self.bind_edge = edge
        self.floor_plan = fp

        # self.dir = self.get_dir()

        self.d_len = 0.1

        self.e_len = None
        self.move_limit = None
        self.ratio = None

        self.new = {
            "v": [],
            "e": [],
            "f": []
        }

        self.is_active = False
        self.is_synced = True

        self.__history = {
            "bind_edge": None,
            "center": None,
        }

    # calculations
    def __cal_limits(self):
        return [
            self.d_len / 2.0 / self.e_len,  # lower limit
            1 - self.d_len / 2.0 / self.e_len,  # upper limit
        ]

    def __cal_ratio(self, pos):
        frac = np.linalg.norm(self.bind_edge.ori.xy - pos) / self.e_len
        if (pos - self.bind_edge.ori.xy) @ self.get_dir() > 0:
            return frac
        else:
            return -frac

    # getters
    def get_dir(self):
        return self.bind_edge.get_dir()

    def get_edge_len(self):
        return self.bind_edge.get_length()

    # setters
    def set_floor_plan(self, fp):
        self.floor_plan = fp

    def set_door_center(self, center):
        assert self.is_active, "Door need to be activate first"

        new_center = center  # closet_position_on_edge(self.bind_edge, pos)
        p = self.__cal_ratio(new_center)
        if not self.__within_limit(p):
            return False

        dir = self.get_dir()
        self.new["v"][0].xy, self.new["v"][1].xy \
            = self.__cut_at_position(new_center)
        self.ratio = p

    # actions
    def activate(self, center, need_correction=True):
        assert self.is_active is False, "Door is already active"
        assert self.bind_edge is not None, "Door is not binded to any edge"
        assert center is not None, "Center is not defined"

        if need_correction:
            center = self.__correct_location(center)

        # init some properties
        self.e_len = self.get_edge_len()
        self.ratio = self.__cal_ratio(center)
        self.move_limit = self.__cal_limits()

        # Reconstruct mesh and add new v e f
        cut_p0, cut_p1 = self.__cut_at_position(center)
        self.new["v"], self.new["e"], self.new["f"] = add_vertex(
            self.bind_edge, cut_p0, Point=FPoint, Edge=FEdge, Face=FFace
        )

        v, e, f = add_vertex(
            self.bind_edge, cut_p1, Point=FPoint, Edge=FEdge, Face=FFace
        )
        self.new["v"] += v
        self.new["e"] += e
        self.new["f"] += f

        e[0].is_blocked = False
        e[1].is_blocked = False  # twin of e[0]
        self.is_active = True

        # set properties
        self.sync_floor_plan()

    def deactivate(self):
        if not self.is_active:
            return

        # 1 -> 0 is working, but 0 -> 1 is not working
        v_del, e_del, f_del = del_vertex(self.new["v"][1])
        v, e, f = del_vertex(self.new["v"][0])
        v_del.extend(v)
        e_del.extend(e)
        f_del.extend(f)

        # for v in v_del:
        #     v.is_active = False
        # for e in e_del:
        #     e.is_active = False
        # for f in f_del:
        #     f.is_active = False

        self.is_active = False
        self.sync_floor_plan()
        self.new = {
            "v": [],
            "e": [],
            "f": []
        }
        # return v_del, e_del, f_del

    def step(self):
        assert self.is_active, "Door is not active"

        self.save_history() # current state

        delta = np.random.normal(0, 0.1)
        # delta = -0.11
        ratio = self.ratio + delta / self.e_len

        if not self.__within_limit(ratio):
            # print("STEP: to next edge")
            self._to_next_edge(ratio)
        else:
            # print("STEP: move")
            self._move_door(delta, ratio)

    def _to_next_edge(self, ratio):
        self.deactivate()
        success = self.__find_next_edge(ratio)
        if not success:
            # manually revert, better reduce the redundant calculation by skipping
            self.activate(self.__history["center"])
        else:
            center = self.__find_next_center(ratio)
            self.activate(center)

    def _move_door(self, delta, ratio):
        self.ratio = ratio
        for v in self.new["v"]:
            v.xy += delta * self.get_dir()

    # utility
    def __correct_location(self, loc):
        if self.bind_edge is None:
            return None
        return closet_position_on_edge(self.bind_edge, loc)

    def __within_limit(self, ratio):
        # print(f"fraction: {self.fraction(pos)} pos: {pos}")
        return self.move_limit[0] <= ratio <= self.move_limit[1]

    def __find_next_edge(self, ratio):
        def search_next_edge(vertex):
            for e in vertex.half_edges:
                if (e.is_inner and e.is_active and
                        not (self.bind_edge is e or
                             e is self.bind_edge.twin)):
                    return e
            return None

        if ratio >= self.move_limit[1]:
            v = self.bind_edge.to
            e = search_next_edge(v)
            if e is None:
                return False
            self.bind_edge = e if e.ori is v else e.twin

        elif ratio <= self.move_limit[0]:
            v = self.bind_edge.ori
            e = search_next_edge(v)
            if e is None:
                return False
            self.bind_edge = e if e.to is v else e.twin

        return True

    def __find_next_center(self, ratio):
        if ratio >= self.move_limit[1]:
            return self.bind_edge.ori.xy + self.get_dir() * self.d_len / 2
        elif ratio <= self.move_limit[0]:
            return self.bind_edge.to.xy - self.get_dir() * self.d_len / 2

    def __init_properties(self):
        # self.dir = self.get_dir()
        self.e_len = self.get_edge_len()
        self.move_limit = self.__cal_limits()
        self.ratio = self.__cal_ratio(self.center)

    def __cut_at_position(self, center):
        # slightly reduce the length of the door to avoid overlap the vertices
        offset = self.get_dir() * self.d_len / 2 * 0.95
        cut_p0 = center + offset
        cut_p1 = center - offset
        return cut_p0, cut_p1

    # properties
    @property
    def center(self):
        return (self.new["v"][0].xy + self.new["v"][1].xy) / 2

    @property
    def vertices(self):
        return self.new["v"]

    @property
    def edges(self):
        return self.new["e"]

    @property
    def faces(self):
        return self.new["f"]

    # history
    def save_history(self):
        self.__history["bind_edge"] = self.bind_edge    # or save eid
        self.__history["center"] = self.center.copy()

    def load_history(self):
        def find_edge(eid):
            for e in self.floor_plan.edges:
                if e.eid == eid:
                    return e
            return None

        if self.bind_edge is self.__history["bind_edge"]:
            # print("=== load history (same) ===")
            # on the same edge
            self.set_door_center(self.__history["center"])
        else:   # on the different edge
            # print("=== load history (diff) ===")
            self.deactivate()
            self.bind_edge = self.__history["bind_edge"]
            # self.bind_edge = find_edge(self.__history["bind_edge"])
            self.activate(self.__history["center"])

    def load_manually(self, edge, center):
        self.deactivate()
        self.bind_edge = edge
        self.activate(center)


    # floor plan
    def sync_floor_plan(self):
        if self.is_active:
            # print("FDoor::sync floor plan - Append")
            self.floor_plan.append(self.new["v"], self.new["e"], self.new["f"])
        else:
            # print("FDoor::sync floor plan - Remove")
            self.floor_plan.remove(self.new["v"], self.new["e"], self.new["f"])


if __name__ == "__main__":
    import numpy as np

    from f_primitives import FPoint, FEdge, FFace
    from u_data_loader import Loader
    from f_layout import FLayout
    from u_geometry import add_vertex

    # settings
    case_id = 1

    np.random.seed(0)
    ld = Loader(".")
    ld.load_closed_rooms_case(case_id)
    ld.optimize()

    nm = FLayout()
    nm.set_default_types(FPoint, FEdge, FFace)
    nm.create_mesh(ld.vertices, ld.edges, 0)
    # nm.reconnect_closed_edges()
    # nm.create_rooms()

    inner_walls = nm.inner_fixed_edges

    e = nm.get_by_eid(12)
    agent = FDoor(e, nm)
    agent.activate(np.array([0.75, 0.75]))
    # for f in nm.faces:
    #     print(f"fid: {f.fid} "
    #           f"| verts: {[v.vid for v in f.verts]} "
    #           f"| adj: {[f.fid for f in f.adjs]}")
    #
    # print("===")
    # agent._to_next_edge(0.999)
    # # agent.sync_floor_plan()
    # for f in nm.faces:
    #     print(f"fid: {f.fid} "
    #           f"| verts: {[v.vid for v in f.verts]} "
    #           f"| adj: {[f.fid for f in f.adjs]}")


    for i in range(85):
        agent.step()
        print("+++")
        for f in nm.faces:
            print(f"fid: {f.fid} | verts: {[v.vid for v in f.verts]}")
        print(f"center: {agent.center} | ratio: {agent.ratio}")
    agent.deactivate()

    from u_visualization import Visualizer

    vis = Visualizer()


    # f37 = FFace.get_by_fid(37)
    # print([v.vid for v in f37.verts])
    # for e in f37.edges:
    #     print(f"eid: {e.eid} | ori: {e.ori.vid} | to: {e.to.vid}")

    # I am not sure the mesh structure is still correct after loading the history or after deactivating the door
    # TODO: I need to visualize the mesh here for debugging
    vis.draw_mesh(nm, show=True, draw_text="vef")
