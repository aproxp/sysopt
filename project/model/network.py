from typing import List
from xml.etree.ElementTree import Element

import networkx as nx

from ortools.sat.python import cp_model

from project.model.link import Link
from project.model.nodes import Node, Switch
from project.model.stream import Stream

import os

import xml.etree.ElementTree as ET


class Network:
    def __init__(self, G, streams):
        self.G = G
        self.streams = streams
        self.model = cp_model.CpModel()

    def frame_constraint(self):
        for stream in self.streams:
            for i in range(len(stream.route)-1):
                src = stream.route[i]
                dst = stream.route[i+1]
                link = self.G.edges[src, dst]
                phi = self.model.NewIntVar(0,
                                           stream.period - link.get_serialization_delay(stream.size),
                                           f'phi_s{stream.id}_l{link.src}-{link.dst}')
                stream._offsets.append(phi)


    def link_overlap_constraint(self):
        pass
        # for node in self.G.nodes:
        #     for s_i in self.streams:
        #         if node not in s_i.route:
        #             continue
        #         for s_j in self.streams:
        #             if s_i == s_j or node not in s_j.route:
        #                 continue

    def route_constraint(self):
        pass

    def end_to_end_constraint(self):
        pass

    def frame_isolation_constraint(self):
        pass


    @classmethod
    def from_xml(cls, xmlfile):
        tree = ET.parse(xmlfile)
        root = tree.getroot()

        G = nx.DiGraph()
        nodes_tmp = root.findall("./device")
        n: Element
        for n in nodes_tmp:
            if n.get('type').lower() != 'switch':
                node = Node.from_xml_element(n)
            else:
                node = Switch.from_xml_element(n)

            G.add_node(node.name, obj=node)

        links_tmp = root.findall("./link")
        for l in links_tmp:
            link = Link.from_xml_element(l)
            G.add_edge(link.src, link.dst, obj=link)

        streams = []
        streams_tmp = root.findall("./stream")
        for s in streams_tmp:
            stream = Stream.from_xml_element(s)
            stream.transform_route(G)
            for link in stream.route:
                link.streams.append(stream)
            streams.append(stream)

        return cls(G, streams)


if __name__ == '__main__':
    net_desc_file = os.path.join(os.path.curdir, '..', 'tctools', 'tc_10s_3h.xml')
    net = Network.from_xml(net_desc_file)
