import networkx as nx
from networkx import Graph


class FanInNeighbours:

    def __init__(self):
        self.network_graph = nx.Graph()
        self.flows = nx.Graph()
        self.paths

    def build(self):
        self.fanin_graph = nx.DiGraph()
        self.fanin_graph.add_nodes_from(self.flows.nodes)
        for p_i in self.paths


