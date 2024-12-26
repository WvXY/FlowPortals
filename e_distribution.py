import matplotlib.pyplot as plt
import numpy as np
from copy import deepcopy

from g_primitives import Point
from f_primitives import RPoint, REdge, RFace
from u_data_loader import Loader
from u_visualization import Visualizer
from f_layout import FloorPlan
from o_door import ODoor

# Settings
case_id = "0a"
np.random.seed(0)

# Load data
ld = Loader(".")
ld.load_w_walls_case(case_id)
ld.optimize()

nm = FloorPlan()
nm.set_default_types(RPoint, REdge, RFace)
nm.create_mesh(ld.vertices, ld.edges, 0)

# Initialize agent
e0 = nm.get_by_eid(0)
agent = ODoor(e0)
agent.activate(np.array([0.5, 0.4]))
nm.append(agent.new_verts, agent.new_edges, agent.new_faces)

sp = np.random.rand(500, 2)
sp = [Point(p) for p in sp]

# Visualization
vis = Visualizer()

def score_func(path):
    return sum(np.linalg.norm(path[i].xy - path[i + 1].xy) for i in range(len(path) - 1))

def f():
    score = 0
    valid_paths = 0
    for i in range(0, 500, 2):
        start = sp[i]
        end = sp[i + 1]
        tripath = nm.find_tripath(start, end)
        path = nm.simplify(tripath, start, end)
        if path:
            valid_paths += 1
            score += score_func(path)
    return score / valid_paths if valid_paths > 0 else float('inf')

# Plot samples
# plt.hist(samples, bins=100, density=True, alpha=0.5, label="Samples")
yy = np.linspace(0.4, 1, 35)
for y in yy:
    agent.set_pos(np.array([0.46875, y]))
    plt.plot(y, f(), 'ro')
# plt.legend()
plt.show()
