from xml.etree.ElementTree import Element

import networkx as nx

from ortools.sat.python import cp_model

from project.model.link import Link
from project.model.nodes import Node, Switch
from project.model.stream import Stream

import os

import xml.etree.ElementTree as ET

from math import lcm

from more_itertools import pairwise


class Network:
    def __init__(self, g, streams):
        self.G = g
        self.streams = streams
        self.model = cp_model.CpModel()
        self.solver = cp_model.CpSolver()
        self.delta = 1

    def frame_constraint(self):
        """Creates the IntVars for the CP-solver.

        """
        mt = None
        for stream in self.streams:
            for link in stream.route:
                if not mt:
                    mt = link.mt
                elif mt != link.mt:
                    raise SystemExit('Only one value of macro-tick supported')

                mul = int(link.mt**-1)

                phi = self.model.NewIntVar(0,
                                           # Serialization delay is already in macro-ticks
                                           stream.period * mul - link.get_serialization_delay(stream.size),
                                           f'phi_s{stream.id}_l{link.src}-{link.dst}')
                stream._offsets.append(phi)

    def link_overlap_constraint(self):
        for e in self.G.edges:
            link = self.G.edges[e]['obj']
            mul = int(link.mt ** -1)
            s_i: Stream
            for s_i in link.streams:
                s_i_phi = s_i._offsets[s_i.route.index(link)]
                s_j: Stream
                for s_j in link.streams:
                    s_j_phi = s_j._offsets[s_j.route.index(link)]
                    if s_i == s_j:
                        continue
                    hp = lcm(s_i.period, s_j.period)
                    # TODO: Verify if integer division is the right thing to do
                    # Must be, since the hp is always divisible by any of the period
                    for alpha in range(0, hp // s_i.period):
                        for beta in range(0, hp // s_j.period):
                            bl = self.model.NewBoolVar(
                                "bl_l{}_s{}_a{}_s{}_b{}".format(link.get_id(), s_i.id, alpha, s_j.id, beta)
                            )


                            self.model.Add(
                                s_i_phi + alpha * s_i.period * mul >=
                                s_j_phi + beta * s_j.period * mul + link.get_serialization_delay(s_j.size)
                            ).OnlyEnforceIf(bl)

                            self.model.Add(
                                s_j_phi + beta * s_j.period * mul >=
                                s_i_phi + alpha * s_i.period * mul + link.get_serialization_delay(s_i.size)
                            ).OnlyEnforceIf(bl.Not())

    def route_constraint(self):
        for stream in self.streams:
            l1: Link
            l2: Link
            for l1, l2 in pairwise(stream.route):
                l1_phi = stream._offsets[stream.route.index(l1)]
                l2_phi = stream._offsets[stream.route.index(l2)]

                mul = int(l1.mt ** -1)

                # multiply both sides of the inequality by mul to get rid of the macrotick
                self.model.Add(
                    l2_phi  - mul * (l2.propagation_delay + self.delta) >=
                    (l1_phi + l1.get_serialization_delay(stream.size))
                )

    def alex_route_constraint(self):
        for stream in self.streams:
            l1: Link
            l2: Link
            for l1, l2 in pairwise(stream.route):
                l1_phi = stream._offsets[stream.route.index(l1)]
                l2_phi = stream._offsets[stream.route.index(l2)]

                sw: Switch = self.G.nodes[1]
                fwd_delay = 0
                if isinstance(sw, Switch):
                    fwd_delay = sw.get_fwd_delay(stream.size)
                link_delay = l1.get_total_delay(stream.size)
                delay = fwd_delay + link_delay

                mul = int(l1.mt ** -1)

                # multiply both sides of the inequality by mul to get rid of the macrotick
                self.model.Add(
                    l2_phi  - mul * (l2.propagation_delay + self.delta) >=
                    (l1_phi + delay)
                )

    def end_to_end_constraint(self):
        for stream in self.streams:
            first: Link = stream.route[0]
            first_phi = stream._offsets[0]
            last: Link = stream.route[-1]
            last_phi = stream._offsets[-1]

            mul = int(first.mt**-1)
            self.model.Add(
                first_phi + mul * stream.deadline >= last_phi + last.get_total_delay(stream.size)
                # first.mt * first_phi + stream.deadline >= last.mt * last_phi + last.get_total_delay(stream.size)
            )

    def frame_isolation_constraint(self):
        for e in self.G.edges:
            link: Link = self.G.edges[e]['obj']
            for s_i in link.streams:
                for s_j in link.streams:
                    if (s_i == s_j) or (s_i.priority != s_j.priority):
                        continue

                    hop_s_i = s_i.route.index(link)
                    hop_s_j = s_j.route.index(link)
                    if hop_s_i == 0 or hop_s_j == 0:
                        continue

                    prev_link_s_i: Link = s_i.route[hop_s_i - 1]
                    prev_link_s_j: Link = s_j.route[hop_s_j - 1]

                    prev_link_s_i_phi = s_i._offsets[hop_s_i - 1]
                    prev_link_s_j_phi = s_j._offsets[hop_s_j - 1]

                    cur_link_s_i_phi = s_i._offsets[hop_s_i]
                    cur_link_s_j_phi = s_j._offsets[hop_s_j]

                    mul = int(link.mt**-1)

                    hp = lcm(s_i.period, s_j.period)
                    # TODO: Verify if integer division is the right thing to do
                    for alpha in range(0, hp // s_i.period):
                        for beta in range(0, hp // s_j.period):
                            bl = self.model.NewBoolVar(
                                "bl_isol_l{}_s{}_a{}_s{}_b{}".format(link.get_id(), s_i.id, alpha, s_j.id, beta)
                            )
                            self.model.Add(
                                cur_link_s_j_phi + mul * (alpha * s_j.period + self.delta) <=
                                prev_link_s_i_phi  + mul * (beta + s_i.period) + prev_link_s_i.get_prop_delay()
                                # cur_link_s_j_phi * link.mt + alpha * s_j.period + self.delta <=
                                # prev_link_s_i_phi * prev_link_s_i.mt + beta + s_i.period + prev_link_s_i.propagation_delay
                            ).OnlyEnforceIf(bl)

                            self.model.Add(
                                cur_link_s_i_phi + mul * (beta * s_i.period + self.delta) <=
                                prev_link_s_j_phi + mul * (alpha + s_j.period) + prev_link_s_j.get_prop_delay()
                                # cur_link_s_i_phi * link.mt + beta * s_i.period + self.delta <=
                                # prev_link_s_j_phi * prev_link_s_j.mt + alpha + s_j.period + prev_link_s_j.propagation_delay
                            ).OnlyEnforceIf(bl.Not())

    def alex_frame_isolation_constraint(self):
        for e in self.G.edges:
            link: Link = self.G.edges[e]['obj']
            for s_i in link.streams:
                for s_j in link.streams:
                    if s_i == s_j:
                        continue

                    hop_s_i = s_i.route.index(link)
                    hop_s_j = s_j.route.index(link)
                    if hop_s_i == 0 or hop_s_j == 0:
                        continue

                    prev_link_s_i: Link = s_i.route[hop_s_i - 1]
                    prev_link_s_j: Link = s_j.route[hop_s_j - 1]

                    prev_link_s_i_phi = s_i._offsets[hop_s_i - 1]
                    prev_link_s_j_phi = s_j._offsets[hop_s_j - 1]

                    cur_link_s_i_phi = s_i._offsets[hop_s_i]
                    cur_link_s_j_phi = s_j._offsets[hop_s_j]

                    mul = int(link.mt**-1)
                    hp = lcm(s_i.period, s_j.period)
                    # TODO: Verify if integer division is the right thing to do
                    for alpha in range(0, hp // s_i.period):
                        for beta in range(0, hp // s_j.period):
                            bl = self.model.NewBoolVar(
                                "bl_isol_l{}_s{}_a{}_s{}_b{}".format(link.get_id(), s_i.id, alpha, s_j.id, beta)
                            )
                            self.model.Add(
                                cur_link_s_j_phi + mul * (alpha * s_j.period + self.delta) <=
                                prev_link_s_i_phi + mul * (beta + s_i.period) + prev_link_s_i.get_total_delay(
                                    s_i.size)
                                # cur_link_s_j_phi * link.mt + alpha * s_j.period + self.delta <=
                                # prev_link_s_i_phi * prev_link_s_i.mt + beta + s_i.period + prev_link_s_i.get_total_delay(
                                #     s_i.size)
                            ).OnlyEnforceIf(bl)

                            self.model.Add(
                                cur_link_s_i_phi + mul * (beta * s_i.period + self.delta) <=
                                prev_link_s_j_phi + mul * (alpha + s_j.period) + prev_link_s_j.get_total_delay(
                                    s_j.size)
                                # cur_link_s_i_phi * link.mt + beta * s_i.period + self.delta <=
                                # prev_link_s_j_phi * prev_link_s_j.mt + alpha + s_j.period + prev_link_s_j.get_total_delay(
                                #     s_j.size)
                            ).OnlyEnforceIf(bl.Not())

    def solve(self):
        return self.solver.Solve(self.model)

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
    net_desc_file = os.path.join(os.path.curdir, '..', 'tctools', 'tc_20s_5h.xml')
    net = Network.from_xml(net_desc_file)
    net.frame_constraint()
    net.link_overlap_constraint()
    net.route_constraint()
    net.end_to_end_constraint()
    net.frame_isolation_constraint()

    status = net.solve()
    if status == cp_model.OPTIMAL:
        print('Optimal solution found')
        for stream in net.streams:
            print(f'Stream: {stream.id}:')
            stream.get_offsets(net.solver)
