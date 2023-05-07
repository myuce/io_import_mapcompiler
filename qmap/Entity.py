from typing import List, Dict, Union
from .Brush import Brush
from .Patch import Patch

class Entity:
    """ Base class that has all the properties and methods used by a map entity. """
    __slots__ = ("id", "properties", "geo", "boundingBox")
    properties: Dict[str, str]
    geo: List[Union[Brush, Patch]]

    def __init__(self, id: int) -> None:
        id: int
        self.id = id
        self.properties = {}
        self.geo = []
        self.boundingBox = None

    def __str__(self) -> str:
        res = "{\n"

        for key, value in self.properties.items():
            res += f'"{key}" "{value}"\n'
        
        for geo in self.geo:
            res += str(geo)

        res += "}\n"

        return res
    
    def __getitem__(self, key: str) -> str:
        return self.properties[key] if key in self.properties else None

    def __setitem__(self, key: str, value: str):
        self.properties[key] = value

    @staticmethod
    def ParseKVP(kvp: str):
        tok = kvp.split('"')

        if len(tok) == 5:
            return tok[1], tok[3]
        elif len(tok) > 5:
            return tok[1], '"'.join(tok[3:-1])

    def __setitem__(self, __name: str, __value: str) -> None:
        self.properties[__name] = __value

    def __getitem__(self, __name: str) -> str:
        return self.properties[__name]

    def __delitem__(self, __name: str) -> None:
        del self.properties[__name]
    
    def __contains__(self, __name: str) -> bool:
        return __name in self.properties
