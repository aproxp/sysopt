# -*- coding: utf-8 -*-
"""
Created on Sun Jan 24 15:51:06 2021

@author: Aleksander
"""

import xml.etree.ElementTree as et
# To try some official implementation
from scipy.optimize import dual_annealing
import random
from math import ceil
import numpy as np
import pandas as pd

# For results consistency
random.seed(10)

# Get tasks, processors and cores
tree = et.parse('../data/small.xml')
root = tree.getroot()
tasks = root.findall("./Application/Task")
mcps = root.findall("./Platform/MCP")
cores = root.findall("./Platform/MCP/Core")

# Sort by priority. Shortest deadline firts, WCET second
tasks.sort(key=lambda task: int(task.get('WCET')))
tasks.sort(key=lambda task: int(task.get('Deadline')))


def avg_laxity(tasks: pd.DataFrame):
    return np.mean(tasks.task_deadline - tasks.wcrt)


# Are the task schedulable?
def dm_guarantee(tasks: pd.DataFrame):
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
            I = sum(ceil(D_i / T_j) * C_j for T_j, C_j in zip(T_js, C_js))
            if I + C_i <= R:
                break
    return True


# What is the worst case response time
def get_wcrts(tasks: pd.DataFrame):
    wcrts = pd.Series(data=np.zeros(len(tasks.index)), dtype='int32')
    for i, x in enumerate(tasks.iterrows()):
        task = x[1]
        I = 0
        while True:
            C_i = float(task['wcet'])
            R = I + C_i
            D_i = float(task['task_deadline'])
            C_js = [float(wcet) for wcet in tasks[0:i]['wcet']]
            T_js = [float(period) for period in tasks[0:i]['task_period']]
            I = sum(ceil(D_i / T_j) * C_j for T_j, C_j in zip(T_js, C_js))
            if I + C_i <= R:
                break
        wcrts[i] = int(R)
    return wcrts


# Get initial solution LEGACY - USES ElementTree objects
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
        solution = np.vstack([solution, asgn])
    return solution


# Check if the schedule is feasible with the given task assignment
def dm_g(df: pd.DataFrame):
    uniq_cores = pd.unique(df['core_uniq'].values)
    for ucore in uniq_cores:
        task_core_asgn = df.loc[(df['core_uniq'] == ucore)]
        if not (dm_guarantee(task_core_asgn)):
            return False
    return True


# cost for annealing. If the schedule is not feasible, it simply returns 1
# if it is, the inverse of average laxity 
def cost(df: pd.DataFrame):
    lax = 0
    if dm_g(df):
        lax = 1
    lax += avg_laxity(df) ** -1
    return lax


solution = rand_solve(tasks, mcps)
df = pd.DataFrame(solution)
dt = {}
attribute_names = ['core_uniq', 'task_id', 'task_deadline', 'task_period', 'task_wcet']
attribute_names += ['mcp_id', 'core_id', 'wcet_fact', 'wcet']
for n in attribute_names:
    if n == 'core_uniq':
        dt[n] = 'string'
    elif n == 'wcet_fact':
        dt[n] = 'float64'
    else:
        dt[n] = 'int32'

df.columns = attribute_names
df = df.astype(dt)


def calc_wcrt(df: pd.DataFrame):
    uniq_cores = pd.unique(df['core_uniq'].values)
    for ucore in uniq_cores:
        task_core_asgn = df.loc[(df['core_uniq'] == ucore)]
        df.loc[task_core_asgn.index, 'wcrt'] = get_wcrts(task_core_asgn).values


def calc_wcet(df: pd.DataFrame):
    df['wcet'] = np.ceil(df['wcet'] * df['wcet_fact']).astype(int)


def rand_move(df: pd.DataFrame, mcps):
    sample = df.sample()
    mcp = random.choice(mcps)
    mid = int(mcp.get('Id'))
    core = random.choice(mcp.findall('Core'))
    cid = int(core.get('Id'))
    while sample.iloc[0]['mcp_id'] == mid and sample.iloc[0]['core_id'] == cid:
        mcp = random.choice(mcps)
        mid = int(mcp.get('Id'))
        core = random.choice(mcp.findall('Core'))
        cid = int(core.get('Id'))
    core_uniq = f"{mid}:{cid}"

    C_fact = float(core.get('WCETFactor'))

    sln = df.copy()
    sln.loc[sample.index, 'core_uniq'] = core_uniq
    sln.loc[sample.index, 'mcp_id'] = mid
    sln.loc[sample.index, 'core_id'] = cid
    sln.loc[sample.index, 'wcet_fact'] = C_fact
    sln.loc[sample.index, 'wcet'] = C_fact * sln.loc[sample.index, 'task_wcet']

    return sln


solution = rand_solve(tasks, mcps)
df = pd.DataFrame(solution)
dt = {}
attribute_names = ['core_uniq', 'task_id', 'task_deadline', 'task_period', 'task_wcet']
attribute_names += ['mcp_id', 'core_id', 'wcet_fact', 'wcet']
for n in attribute_names:
    if n == 'core_uniq':
        dt[n] = 'string'
    elif n == 'wcet_fact':
        dt[n] = 'float64'
    else:
        dt[n] = 'int32'

df.columns = attribute_names
df = df.astype(dt)
calc_wcrt(df)


def calc_beta(cur_cost, cand_cost, T):
    rand = random.random()
    if T < 0.4:
        if rand > 0.2:
            return False
        return True
    else:
        if rand > 0.4:
            return False
        return True


def annealing(init: pd.DataFrame, mcps):
    T = 1.0
    T_accept = 0.000001
    alpha = 0.99
    df = init.copy()
    while T > T_accept:
        cand = rand_move(df, mcps)
        calc_wcrt(cand)
        beta = calc_beta(cost(df), cost(cand), T)
        if cost(cand) < cost(df):
            df = cand
        else:
            if beta:
                df = cand
        T = T * alpha
    return df
