from dataclasses import dataclass, field
from math import ceil

from typing import List


@dataclass
class Link:
    src: str
    dst: str
    speed: float = 1250 # Bytes per micro second

    propagation_delay: float = 0 # us, property of the switch, modelled here per port
    ingress_processing_delay: float = 0 # us, property of the switch, modelled here per port
    egress_processing_delay: float = 0 # us, property of the switch, modelled here per port
    streams: List['Stream'] = field(default_factory=list)
    streams_offsets: List[int] = field(default_factory=list)
    # mt: float = 0.01

    def as_xml(self):
        return f'<link src="{self.src}" dst="{self.dst}" speed="{self.speed}"/>'

    def get_id(self):
        return f'{self.src}-{self.dst}'

    def get_serialization_delay(self, size):
        """Get serialization delay in N macroticks

        :param size: size of frame in bytes (int)
        :return:
        """
        return int(ceil(size / (self.speed * 1e6)))

    def get_prop_delay(self):
        return int(ceil(self.propagation_delay))

    def get_ip_delay(self):
        return int(ceil(self.ingress_processing_delay))

    def get_ep_delay(self):
        return int(ceil(self.egress_processing_delay))

    def get_total_delay(self, size):
        return self.get_prop_delay() + self.get_ip_delay() + self.get_ep_delay() + self.get_serialization_delay(size)

    @classmethod
    def from_xml_element(cls, e):
        return cls(
            str(e.get('src')),
            str(e.get('dst')),
            float(e.get('speed'))
        )

