from typing import Dict

class Material:
    __slots__ = ("name", "shader", "data")

    name: str
    shader: str
    data: Dict[str, str]

    def __init__(self, name, shader) -> None:
        self.name = name
        self.shader = shader
        self.data = {}
