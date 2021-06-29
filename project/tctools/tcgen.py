import random
from enum import Enum
from xml.dom import minidom

import matplotlib.pyplot as plt
import networkx as nx

from project.model.link import Link
from project.model.nodes import Switch
from project.model.stream import Stream


class Topology(Enum):
    FULL_MESH = 1


class Routing(Enum):
    DISABLED = 1
    SHORTEST_PATH = 2
    RANDOM = 3


class Tc:
    def __init__(self,
                 id: str,
                 network: nx.DiGraph,
                 streams: list):
        self.id = id
        self.network = network
        self.streams = streams

    def as_xml(self) -> str:
        retval = '<NetworkDescription>'
        for node in self.network.nodes:
            retval += f'<device name="{node}" type="Switch"/>'
        for edge in self.network.edges:
            link = self.network.edges[edge]['obj']
            retval += f'{link.as_xml()}'

        for s in self.streams:
            retval += f'{s.as_xml(with_route=True)}'

        retval += '</NetworkDescription>'
        return retval

    def plot(self):
        fig = plt.figure()
        nx.draw(self.network, with_labels=True)
        plt.show()


class TcGen:

    def __init__(self,
                 stream_range,
                 hops_range,
                 topology=Topology.FULL_MESH,
                 routing=Routing.RANDOM
                 ):
        self.stream_range = stream_range
        self.hops_range = hops_range
        self.topology = topology
        self.routing = routing

    def generate_testcases(self):
        for n_hops in self.hops_range:
            n_nodes = max(5, n_hops)

            if self.topology == Topology.FULL_MESH:
                network = nx.complete_graph(n_nodes, nx.DiGraph())
            else:
                raise SystemExit("Only full mesh topologies supported")

            for n in network.nodes:
                s = Switch(n)
                network.nodes[n]['obj'] = s

            for e in network.edges:
                link = Link(e[0], e[1])
                network.edges[e]['obj'] = link

            for n_streams in self.stream_range:
                streams = []
                for s in range(n_streams):
                    src = random.randint(0, n_nodes - 1)
                    dst = random.randint(0, n_nodes - 1)
                    while dst == src:
                        dst = random.randint(0, n_nodes - 1)
                    size = random.randint(64, 1500)
                    period = 2 ** (random.randint(2, 5))
                    deadline = period
                    nodes = list(range(n_nodes))
                    nodes.remove(src)
                    nodes.remove(dst)
                    path = random.sample(nodes, n_hops - 2)
                    path = [src] + path + [dst]

                    stream = Stream(str(s), str(src), str(dst), size, period, deadline, 0, path)
                    streams.append(stream)
                tc_id = f'{n_streams}s_{n_hops}h'
                tc = Tc(tc_id, network, streams)
                with open(f'tc_{tc_id}.xml', 'w') as f:
                    s = minidom.parseString(tc.as_xml()).toprettyxml(indent="    ")
                    f.write(s)


if __name__ == '__main__':
    stream_range = list(range(10, 50, 10))
    hops_range = list(range(3, 8, 1))
    topology = Topology.FULL_MESH
    routing = Routing.RANDOM
    tcgen = TcGen(stream_range, hops_range)
    tcgen.generate_testcases()
