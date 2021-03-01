import importlib
import random
from copy import deepcopy
from xml.dom import minidom

import model

importlib.reload(model)
import xml.etree.ElementTree as ET
import os
import pandas as pd
import matplotlib.style
matplotlib.style.use('ggplot')
import seaborn as sns
import matplotlib.pyplot as plt

random.seed(10)

DATA_SMALL = os.path.join("data", 'small.xml')
DATA_MEDIUM = os.path.join("data", 'medium.xml')
DATA_LARGE = os.path.join("data", 'large.xml')
DATA_IN = DATA_LARGE

# %% Parse
tree = ET.parse(DATA_IN)
root = tree.getroot()

tasks = []
tasks_tmp = root.findall("./Application/Task")
for t in tasks_tmp:
    task = model.Task(t.get('Deadline'), t.get('Id'), t.get('Period'), t.get('WCET'))
    tasks.append(task)
n_tasks = len(tasks)

cores = []
mcps_tmp = root.findall("./Platform/MCP")

for m in mcps_tmp:
    for c in m.findall('Core'):
        core = model.Core(m.get("Id"), c.get("Id"), c.get("WCETFactor"))
        cores.append(core)

# %% Uniform assignment
for i, task in enumerate(tasks):
    core = cores[i % len(cores)]
    core.assign_task(task)
# %%
for core in cores:
    core.sort_tasks()
    core.dm_guarantee()


# %%
def avg_laxity(cores):
    lax = 0
    n = 0
    for core in cores:
        for task in core.tasks:
            lax += task.get_laxity()
            n += 1

    return lax / n


def cost(cores):
    schedulable = all([core.dm_guarantee() for core in cores])
    if schedulable:
        return avg_laxity(cores) ** -1
    else:
        return 0.1 + (avg_laxity(cores) ** -1)


def rand_swap(cores_in):
    cores = deepcopy(cores_in)
    core_1 = random.choice(cores)
    core_2 = random.choice(cores)
    while core_1 == core_2:
        core_2 = random.choice(cores)
    task_1 = core_1.tasks.pop(random.randrange(len(core_1.tasks)))
    task_2 = core_2.tasks.pop(random.randrange(len(core_2.tasks)))
    core_1.assign_task(task_2)
    core_1.sort_tasks()
    core_2.assign_task(task_1)
    core_2.sort_tasks()
    return cores


def calc_beta(cur_cost, cand_cost, T):
    rand = random.random()
    if T < 0.4:
        if rand > 0.1:
            return False
        return True
    else:
        if rand > 0.4:
            return False
        return True


def annealing(cores_in):
    stats = {}
    stats['i'] = 0
    stats['worse_acc'] = 0
    stats['better_acc'] = 0
    stats['laxities'] = []
    stats['schedulable'] = []

    cores = cores_in
    T = 1.0
    T_accept = 0.00001
    alpha = 0.99
    while T > T_accept:
        stats['i'] += 1
        stats['schedulable'].append(all([core.dm_guarantee() for core in cores]))
        cand = rand_swap(cores)
        cand_cost = cost(cand)
        cur_cost = cost(cores)
        cand_sch = all([core.dm_guarantee() for core in cand])
        beta = calc_beta(cur_cost, cand_cost, T)
        if cand_cost < cur_cost:
            cores = cand
            stats['better_acc'] += 1
        else:
            if beta and cand_sch:
                stats['worse_acc'] += 1
                cores = cand
        stats['laxities'].append(avg_laxity(cores))
        T = T * alpha
    lax = avg_laxity(cores)
    sch = all([core.dm_guarantee() for core in cores])
    return sch, lax, cores, stats


# %% Run the annealing
sch, lax, cores, stats = annealing(cores)

# %% XML export
sol = ET.ElementTree
sol = ET.Element('solution')
for core in cores:
    for task in core.tasks:
        attribs = {}
        attribs["Id"] = str(task.id)
        attribs["MCP"] = str(core.mid)
        attribs["Core"] = str(core.id)
        attribs["WCRT"] = str(task.wcrt)
        child = ET.SubElement(sol, 'Task', attrib=attribs)
comment = ET.Comment(f"Average laxity: {lax}")
s = minidom.parseString(ET.tostring(sol, encoding='unicode')).toprettyxml(indent="    ")
file_out = os.path.join('solutions', 'sol.xml')
with open(file_out, 'w') as f:
    f.write(s)

# %% Plot laxity evolution in iteration
df = pd.DataFrame(data=stats['laxities'], columns=["Avg. laxity"])
df['Schedulable'] = stats['schedulable']
sns.scatterplot(data=df, x=df.index, y='Avg. laxity', hue='Schedulable')
f = os.path.join('solutions', 'sol.svg')
plt.savefig(f, bbox_inches='tight')
plt.show()
