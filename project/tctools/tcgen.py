import random
import xml.etree.ElementTree as ET
from enum import Enum
import networkx as nx
from project.model.stream import Stream
import matplotlib.pyplot as plt


class Topology(Enum):
    FULL_MESH = 1


class Tc():
    def __init__(self,
                 id : str,
                 network: nx.DiGraph,
                 streams: list):
        self.id = id
        self.network = network
        self.streams = streams

    def as_xml(self) -> str:
        retval = '<NetworkDescription>'
        for node in self.network.nodes:
            retval += f'    <device name="{node}" type="Switch"/>\n'
        for edge in self.network.edges:
            retval += f'    <link src="{edge[0]}" dst="{edge[1]}" speed="1"/>\n'

        for s in self.streams:
            retval += f'    {s.as_xml()}\n'

        retval += '</NetworkDescription>'
        return retval

    def plot(self):
        fig = plt.figure()
        nx.draw(self.network, with_labels=True)
        plt.show()




class TcGen:
    default_cfg = {
        'stream_range': list(range(10, 50, 10)),
        'hops_range': list(range(3, 8, 1)),
        'topology': Topology.FULL_MESH
    }

    def __init__(self,
                 cfg=default_cfg
                 ):
        self.stream_range = *cfg['stream_range'],
        self.hops_range = *cfg['hops_range'],
        self.topology = cfg['topology']

    def generate_testcases(self):
        for n_hops in self.hops_range:
            n_nodes = max(5, n_hops)

            if self.topology == Topology.FULL_MESH:
                network = (nx.generators.complete_graph(n_nodes)).to_directed()
            else:
                raise SystemExit("Only full mesh topologies supported")

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

                    stream = Stream(s, src, dst, size, period, deadline, path)
                    streams.append(stream)
                tc_id = f'{n_streams}s_{n_hops}h'
                tc = Tc(tc_id, network, streams)
                with open(f'tc_{tc_id}.xml', 'w') as f:
                    f.write(tc.as_xml())


if __name__ == '__main__':
    tcgen = TcGen()
    tcgen.generate_testcases()
