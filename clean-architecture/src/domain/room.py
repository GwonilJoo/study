import uuid
from dataclasses import dataclass, asdict
from typing import Dict, Any


@dataclass
class Room:
    code: uuid.UUID
    size: int
    price: int
    longitude: float
    latitude: float

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        return cls(**data)
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)