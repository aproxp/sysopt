import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import List

import networkx as nx
from ortools.sat.python.cp_model import IntVar, CpSolver


@dataclass
class Stream:
    """This class models network streams.

    Stream objects represent periodic network flows. During scheduling, each stream is assigned an offset phi on
    each subsequent link along the route.

    Args:
        id (int or string): unique stream identifier
        src (int): source network node
        dst (int): dst network node
        size (int): bytes, size of the stream (in this implementation streams are supposed to fit in one frame)
        deadline (float): microseconds, how long does the stream have to reach the dst
        period (float): microseconds, new stream instance (frame) is created each period

        priority (int): queue mapping route (List[Node]): ordered list of nodes traversed from source to dst.
        With a network graph can be transformed into list of edges (link objects)

         _offsets (List[IntVar]): list of offsets phi on each link along the route. Actual value is obtained by running
         the solver and calling solver.Value(_offsets[i])
    """
    id: str
    src: str
    dst: str
    size: int
    period: int
    deadline: int

    priority: int = 0
    route: list = field(default_factory=list)
    _offsets: List[IntVar] = field(default_factory=list, init=False)

    def get_offsets(self, solution: CpSolver):
        for link, phi in zip(self.route, self._offsets):
            print(f'{link.get_id()}: {solution.Value(phi)}')

    def as_xml(self, with_route=False) -> str:
        """

        :param with_route: boolean, route will be added as an xml collection
        :return:
        :return: XML representation of the stream
        :rtype: str
        """
        if not with_route:
            retval = '<stream id="{}" src="{}" dest="{}" size="{}" period="{}" deadline="{}"/>'.format(
                self.id,
                self.src,
                self.dst,
                self.size,
                self.period,
                self.deadline
            )
        else:
            retval = '<stream id="{}" src="{}" dest="{}" size="{}" period="{}" deadline="{}">'.format(
                self.id,
                self.src,
                self.dst,
                self.size,
                self.period,
                self.deadline,
                self.route_as_xml()
            )
            retval += self.route_as_xml()
            retval += f'</stream>'
        return retval

    def route_as_xml(self, link_view=True):
        retval = f'<route>'
        if not link_view:
            for n in self.route:
                retval += f'<node id="{n}" />'
        else:
            for i, l in enumerate(self.route):
                if i == len(self.route) - 1:
                    break
                retval += f'<link src="{l}" dest="{self.route[i + 1]}" />'

        retval += f'</route>'
        return retval

    @classmethod
    def from_xml_element(cls, e: ET.Element):
        links = list(e.find('./route'))
        route = []
        for l in links:
            route.append((l.get('src'), l.get('dest')))

        return cls(id=str(e.get('id')),
                   src=str(e.get('src')),
                   dst=str(e.get('dest')),
                   size=int(e.get('size')),
                   period=int(e.get('period')),
                   deadline=int(e.get('deadline')),
                   route=route
                   )
    def transform_route(self, G: nx.DiGraph):
        new_route = []
        for link in self.route:
            new_route.append(G.edges[link]['obj'])
        self.route = new_route

