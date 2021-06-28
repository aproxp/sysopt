from dataclasses import dataclass, field

from typing import List


@dataclass
class Link:
    src: str
    dst: str
    speed: float = 1.25 # Bytes per second

    propagation_delay: float = 0
    ingress_processing_delay: float = 0 # us, property of the switch, modelled here per port
    egress_processing_delay: float = 0
    streams: List['Stream'] = field(default_factory=list)
    streams_offsets: List[int] = field(default_factory=list)

    def as_xml(self):
        return f'<link src="{self.src}" dst="{self.dst}" speed="{self.speed}"/>'

    def get_id(self):
        return f'{self.src}-{self.dst}'

    def get_serialization_delay(self, size):
        return int(size / self.speed * 10e6)

    def get_total_delay(self, size):
        return self.propagation_delay + self.ingress_processing_delay + self.egress_processing_delay + self.get_serialization_delay(size)

    @classmethod
    def from_xml_element(cls, e):
        return cls(
            str(e.get('src')),
            str(e.get('dst')),
            float(e.get('speed'))
        )

