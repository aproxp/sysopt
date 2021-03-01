from math import ceil

class Task:
    def __init__(self, deadline, tid, period, wcet):
        self.deadline = int(deadline)
        self.period = int(period)
        self.id = int(tid)
        self.wcet = int(wcet)

        self.wcrt = 0
        self.wcet_adjusted = int(wcet)

    def __str__(self):
        return f"Id: {self.id}, Deadline: {self.deadline}, Period: {self.period}, WCET: {self.wcet}, WCET_ADJ: {self.wcet_adjusted}, WCRT: {self.wcrt}"

    def get_laxity(self):
        return self.deadline - self.wcrt


class Platform:
    def __init__(self):
        self.mcps = []


class Mcp:
    def __init__(self, mid):
        self.id = mid
        self.cores = []


class Core:
    def __init__(self, mid, cid, wcet_fact):
        self.wcet_fact = float(wcet_fact)
        self.id = cid
        self.mid = mid
        self.tasks = []

    def sort_tasks(self):
        self.tasks.sort(key=lambda task: task.wcet)
        self.tasks.sort(key=lambda task: task.deadline)

    def assign_task(self, task):
        task.wcet_adjusted = int(ceil(task.wcet * self.wcet_fact))
        self.tasks.append(task)

    def dm_guarantee(self):
        for i, task in enumerate(self.tasks):
            I = 0
            while True:
                C_i = float(task.wcet)
                R = I + C_i
                task.wcrt = int(R)
                D_i = float(task.deadline)
                if R > D_i:
                    return False
                C_js = [float(task.wcet) for task in self.tasks[0:i]]
                T_js = [float(task.period) for task in self.tasks[0:i]]
                I = sum(ceil(D_i / T_j) * C_j for T_j, C_j in zip(T_js, C_js))
                if I + C_i <= R:
                    break
        return True

    def __str__(self):
        s = f"Core: {self.id} at MCP: {self.mid}. WCET_FACT: {self.wcet_fact}\n"
        for task in self.tasks:
            s += f"\t {task}\n"

        return s



class Solution:
    def __init__(self):
        self.laxity = 0
        self.tasks = []
