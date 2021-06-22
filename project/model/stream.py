from dataclasses import dataclass


@dataclass
class Stream:
    id: int
    source: int
    destination: int
    size: int
    deadline: int
    period: int

    route: list

    def as_xml(self) -> str:
        return '<stream id="{}" src="{}" dest="{}" size="{}" period="{}" deadline="{}"/>'.format(
            self.id,
            self.source,
            self.destination,
            self.size,
            self.period,
            self.deadline
        )