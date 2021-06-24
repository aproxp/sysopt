from dataclasses import dataclass, field

from typing import List


@dataclass
class Node:
    name: str
    streams: List['Stream'] = field(default_factory=list)

    @classmethod
    def from_xml_element(cls, e):
        return cls(name=e.get('name'))


@dataclass
class Switch(Node):
    fwd_speed: float = field(default=1.25)  # Bytes per second

    def get_fwd_delay(self, size: int) -> int:
        """

        :rtype: int
        :param size: frame size in bytes
        :return: forwarding delay in microseconds
        """
        return int(size / self.fwd_speed * 10e6)

    def get_worst_case_fwd_delay(self, stream: 'Stream') -> int:
        """

        :rtype: int
        :param stream: stream to get worst case forwarding delay for
        :return:
        """
        delay: int = self.get_fwd_delay(stream.size)
        for s in self.streams:
            if stream.priority < s.priority:
                delay += self.get_fwd_delay(s.size)
            elif stream.priority == s.priority:
                delay += min(self.get_fwd_delay(stream.size), self.get_fwd_delay(s.size))
        return delay

    # @classmethod
    # def from_xml_element(cls, e):
    #     return cls(int(e.get('id')),
    #                name=e.get('name')
    #                )
