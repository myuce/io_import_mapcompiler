from typing import List, Tuple
from Math.Vector3 import Vector3
from Math.Vector2 import Vector2

PolyVert = Tuple[int, int, int] # position uv normal
Triangle = Tuple[int, PolyVert, PolyVert, PolyVert] # material idx vert vert vert

def Tri2Str(tri: Triangle):
    return f"f {tri[1][0] + 1}/{tri[1][1] + 1}/{tri[1][2] + 1} {tri[2][0] + 1}/{tri[2][1] + 1}/{tri[2][2] + 1} {tri[3][0] + 1}/{tri[3][1] + 1}/{tri[3][2] + 1}"

class Group:
    __slots__ = ("vertices", "uvs", "normals", "name", "faces")

    vertices: List[Vector3]
    uvs: List[Vector2]
    normals: List[Vector3]
    name: str
    faces: List[Triangle]

    def __init__(self, name: str) -> None:
        self.vertices = []
        self.uvs = []
        self.normals = []
        self.name = name
        self.faces = []

class Model:
    __slots__ = ("groups", "materials", "modelData")

    groups: List[Group]
    materials: List[str]

    def __init__(self) -> None:
        self.groups = []
        self.materials = []
