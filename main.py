import numpy as np

# from time import time

from geometry import Point
from visualizer import Visualizer
from navmesh import NavMesh
from loader import Loader

# from optimizer import Optimizer

np.random.seed(0)
ld = Loader(".")
ld.load_w_walls_case(6)

nm = NavMesh()
nm.create(ld.vertices, ld.indices, 0)
vis = Visualizer()
vis.draw_mesh(nm, show=False)

# for i in range(80):
#     start = Point(np.random.rand(2))
#     end = Point(np.random.rand(2))
#     c = np.random.rand(3)
#
#     tripath = nm.find_tripath(start, end)
#     if tripath is None:
#         print("No path found")
#         continue
#     path = nm.simplify(tripath, start, end)
#
#     # vis.draw_tripath(tripath)
#     vis.draw_point(start, c="g", s=40, m="s")
#     vis.draw_point(end, c="r", s=40)
#     vis.draw_linepath(path, c=c, s=1.2)

start = Point(np.array([0.2, 0.3]))
end = Point(np.array([0.1, 0.6]))
c = np.random.rand(3)

tripath = nm.find_tripath(start, end)

if tripath is None:
    print("No path found")
    vis.show("Mesh")
    exit()

path = nm.simplify(tripath, start, end)

vis.draw_tripath(tripath)
vis.draw_point(start, c="g", s=40, m="s")
vis.draw_point(end, c="r", s=40)
vis.draw_linepath(path, c=c, s=1.2)

vis.show("navmesh")
