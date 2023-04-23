from mathutils import Vector
from math import ceil
import numpy as np
from typing import List, Tuple, Union
from ..func.Helpers import Vec2Str

class PatchVert:
    __slots__ = ("pos", "uv")
    pos: Vector
    uv: Vector

    def __init__(self, pos: Vector, uv: Vector) -> None:
        self.pos, self.uv = pos, uv

    def __add__(self, rhs: 'PatchVert') -> 'PatchVert':
        return PatchVert(
            self.pos + rhs.pos,
            self.uv + rhs.uv
        )

    def __mul__(self, rhs: Union['PatchVert', float]) -> 'PatchVert':
        if isinstance(rhs, PatchVert):
            return PatchVert(
                self.pos * rhs.pos,
                self.uv * rhs.uv
            )
        else:
            return PatchVert(
                self.pos * rhs,
                self.uv * rhs
            )

    def __str__(self) -> str:
        return f"( {Vec2Str(self.pos)} {Vec2Str(self.uv)} )"

    @staticmethod
    def FromStr(row: str) -> List['PatchVert']:
        tok = row.strip()[2:-2].split()
        res: List[PatchVert] = []
        
        for vert in [tok[v + 1:v + 6] for v in range(0, len(tok), 7)]:
            vert = [float(v) for v in vert]
            res.append(PatchVert(
                Vector([float(i) for i in vert[0:3]]),
                Vector((float(vert[3]), float(vert[4])))
            ))

        return res

class Patch:
    __slots__ = ("size", "material", "verts")
    size: Tuple[int, int]
    material: str
    verts: List[List[PatchVert]]

    def __init__(self, size: Tuple[int, int], material: str) -> None:
        self.size = size
        self.material = material
        self.verts = []

    def __str__(self) -> str:
        res = "{\n"
        res += "patchDef2\n"
        res += "{\n"
        res += self.material + "\n"
        res += f"( {self.size[0]} {self.size[1]} 0 0 0 )\n"
        res += "(\n"
        
        for row in self.verts:
            res += "( " + " ".join([str(vert) for vert in row]) + " )\n"

        res += ")\n"
        res += "}\n"
        res += "}\n"

        return res

    def Slice(self, maxSize: int=16) -> List['Patch']:
        if self.size[0] <= maxSize and self.size[1] <= maxSize:
            return [self]
        
        res: List['Patch'] = []

        # create a 2d numpy array of vertices
        arr: np.ndarray = np.array(self.verts)

        # slice the 2d array into smaller 2d arrays
        numvert = ceil((len(arr) - 1) / (maxSize - 1))
        numhorz = ceil((len(arr[0]) - 1) / (maxSize - 1))

        for i in range(numvert):
            for j in range(numhorz):
                startvert = i * (maxSize - 1)
                endvert = (i + 1) * (maxSize - 1) + 1
                starthorz = j * (maxSize - 1)
                endhorz = (j + 1) * (maxSize - 1) + 1

                if endvert > len(arr):
                    endvert = len(arr)
                if endhorz > len(arr[0]):
                    endhorz = len(arr[0])
                
                newarr = arr[startvert:endvert, starthorz:endhorz].tolist()

                newPatch = Patch((len(newarr), len(newarr[0])), self.material)
                newPatch.verts = newarr
                res.append(newPatch)

        return res

