# -*- coding: utf-8 -*-
"""
Created on Sun Jan 24 15:51:06 2021

@author: Aleksander
"""

import xml.etree.ElementTree as ET
from scipy.optimize import dual_annealing
import random
from math import ceil
import numpy as np
import pandas as pd
from collections import OrderedDict
tree = ET.parse('small.xml')
root = tree.getroot()

# for app in root.iter('Application.Task'):
#     print(app.tag, app.attrib)

tasks = root.findall("./Application/Task")
mcps = root.findall("./Platform/MCP")
cores = root.findall("./Platform/MCP/Core")

tasks.sort(key = lambda task: int(task.get('WCET')))
tasks.sort(key = lambda task: int(task.get('Deadline')))
# for task in tasks:
#     print(task.get('Id'), task.get('Period'), task.get('WCET'))
    
# for mcp in mcps:
#     print(mcp.tag, mcp.attrib)
#     print(list(mcp))

def laxity(task):
    return float(task.get('Deadline')) - float(task.get('WCET'))

def dm_guarantee(tasks):
    for i, task in tasks.iterrows():
        I = 0
        while True:
            C_i = float(task['wcet'])
            R = I + C_i
            D_i = float(task['task_deadline'])
            if R > D_i:
                return False
            C_js = [float(wcet) for wcet in tasks[0:i]['wcet']]
            T_js = [float(period) for period in tasks[0:i]['task_period']]
            I = sum(ceil(D_i/T_j)*C_j for T_j, C_j in zip(T_js, C_js))
            if I + C_i <= R:
                break
    return True

def get_wcrt(tasks):
    for i, task in tasks.iterrows():
        I = 0
        while True:
            C_i = float(task['wcet'])
            R = I + C_i
            D_i = float(task['task_deadline'])
            if R > D_i:
                return False
            C_js = [float(wcet) for wcet in tasks[0:i]['wcet']]
            T_js = [float(period) for period in tasks[0:i]['task_period']]
            I = sum(ceil(D_i/T_j)*C_j for T_j, C_j in zip(T_js, C_js))
            if I + C_i <= R:
                break
    return True
            

def rand_solve(tasks, mcps):
    solution = np.empty((0, 9))
    for task in tasks:
        tid = int(task.get('Id'))
        D = int(task.get('Deadline'))
        T = int(task.get('Period'))
        C = int(task.get('WCET'))
        mcp = random.choice(mcps)
        mid = int(mcp.get('Id'))
        core = random.choice(mcp.findall('Core'))
        cid = int(core.get('Id'))
        C_fact = float(core.get('WCETFactor'))
        C_hat = int(ceil(float(C) * C_fact))
        core_uniq = f"{mid}:{cid}"
        asgn = np.array([core_uniq, tid, D, T, C, mid, cid, C_fact, C_hat])
        # print(asgn)
        solution = np.vstack([solution, asgn])
    return solution

solution = rand_solve(tasks, mcps)
df = pd.DataFrame(solution)
attribute_names = ['core_uniq', 'task_id', 'task_deadline', 'task_period', 'task_wcet']
attribute_names += ['mcp_id', 'core_id', 'wcet_fact', 'wcet']
df.columns = attribute_names

uniq_cores = pd.unique(df['core_uniq'].values)

for ucore in uniq_cores:
    # print(ucore)
    # print(df.loc[(df['core_uniq']==ucore)])
    task_core_asgn = df.loc[(df['core_uniq']==ucore)]
    print(dm_guarantee(task_core_asgn))
    
#df.loc[(df['core_id']=='0') & (df['mcp_id']=='0')]
        
# def dm_guarantee(tasks):
#     for i, task in enumerate(tasks):
#         I = 0
#         while True:
#             C_i = float(task.get('WCET'))
#             R = I + C_i
#             D_i = float(task.get('Deadline'))
#             if R > D_i:
#                 return False
#             C_js = [float(task.get('WCET')) for task in tasks[0:i]]
#             T_js = [float(task.get('Period')) for task in tasks[0:i]]
#             I = sum(ceil(D_i/T_j)*C_j for T_j, C_j in zip(T_js, C_js))
#             # print(f"Task: {i}")
#             # print(f"C_i: {C_i}")
#             # print(f"D_i: {D_i}")
#             # print(f"R: {R}")
#             # print(f"I: {I}")
#             # print("=============")
#             if I + C_i <= R:
#                 break
#     return True
            


def annealing():
    solutions = generateSolutions()
    random_index = random.randint(0, len(solutions) - 1)
    T = 1.0
    T_accept = 0.0000001
    alpha = .99
    s = solutions[random_index]
    while T > T_accept:
        s_new = randomNeighbor(s, solutions)
        beta = betaFunc(cost(s), cost(s_new), T)
        if cost(s_new) < cost(s):
            s = s_new
        else:
            if beta:
                s = s_new
        T = T * alpha
    return s

def randomNeighbor(sln, solutions):
    currentIndex = solutions.index(sln)
    randomStep = random.randint(1, 2)
    if randomStep == 1:
        if currentIndex > 0:
            return solutions[currentIndex - 1]
        else:
            return solutions[currentIndex + 1]
    elif randomStep == 2:
        if currentIndex < len(solutions) - 1:
            return solutions[currentIndex + 1]
        else:
            return solutions[currentIndex - 1]

def cost(sln):
    return abs(401 - sln)

def betaFunc(oldCost, newCost, T):
    rand = random.random()
    if T < 0.4:
        if rand > 0.2:
            return False
        return True
    else:
        if rand > 0.4:
            return False
        return True

def generateSolutions():
    nums = []
    for a in range(1, 500, 2):
        nums.append(a)
    for a in range(0, 499, 2):
        nums.append(500 - a)
    return nums