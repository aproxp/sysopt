from dataclasses import dataclass, field

from typing import List

from project.model.nodes import Node

from ortools.sat.python.cp_model import IntVar


@dataclass
class Stream:
    """This class models network streams.

    Stream objects represent periodic network flows. During scheduling, each stream is assigned an offset phi on
    each subsequent link along the route.

    Args:
        id (int): unique stream identifier
        source (int): source network node
        destination (int): destination network node
        size (int): bytes, size of the stream (in this implementation streams are supposed to fit in one frame)
        deadline (int): microseconds, how long does the stream have to reach the destination
        period (int): microseconds, new stream instance (frame) is created each period

        priority (int): queue mapping route (List[Node]): ordered list of nodes traversed from source to destination.
        With a network graph can be transformed into list of edges (link objects) _offsets (List[IntVar]): list of
        offsets phi on each link along the route. Actual value is obtained by running the solver and calling
        solver.Value(_offsets[i])
    """
    id: int
    source: int
    destination: int
    size: int
    period: int
    deadline: int

    priority: int = 0
    route: List[Node] = field(default_factory=list)
    _offsets: List[IntVar] = field(default_factory=list, init=False)

    def as_xml(self, with_route=False, indent_level=0) -> str:
        """

        :return: XML representation of the stream
        :rtype: str
        """
        ind = indent_level * '    '
        if not with_route:
            retval = '{}<stream id="{}" src="{}" dest="{}" size="{}" period="{}" deadline="{}"/>'.format(
                ind,
                self.id,
                self.source,
                self.destination,
                self.size,
                self.period,
                self.deadline
            )
        else:
            retval = '{}<stream id="{}" src="{}" dest="{}" size="{}" period="{}" deadline="{}">\n'.format(
                ind,
                self.id,
                self.source,
                self.destination,
                self.size,
                self.period,
                self.deadline,
                self.route_as_xml()
            )
            retval += self.route_as_xml(indent_level=indent_level+1)
            retval += f'{ind}</stream>\n'
        return retval

    def route_as_xml(self, link_view=True, indent_level=0):
        ind = indent_level * '    '
        retval = f'{ind}<route>\n'
        if not link_view:
            for l in self.route:
                retval += f'{ind}    <node id="{l}" />\n'
        else:
            for i, l in enumerate(self.route):
                if i == len(self.route)-1:
                    break
                retval += f'{ind}    <link src="{l}" dst="{self.route[i+1]}" />\n'

        retval += f'{ind}</route>\n'
        return retval

    @classmethod
    def from_xml_element(cls, e):
        return cls(int(e.get('id')),
                   int(e.get('src')),
                   int(e.get('dest')),
                   int(e.get('size')),
                   int(e.get('period')),
                   int(e.get('deadline'))
                   )
