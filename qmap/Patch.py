import bpy
from mathutils import Vector
from math import ceil
import numpy as np
from typing import List, Tuple, Union
from ..func.Helpers import Vec2Str

class PatchVert:
    __slots__ = ("pos", "uv", "lm")
    pos: Vector
    uv: Vector
    lm: Vector

    def __init__(self, pos: Vector, uv: Vector) -> None:
        self.pos, self.uv, self.lm = pos, uv, None

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
    __slots__ = ("size", "material", "verts", "calculatedVerts", "bpy_obj")
    size: Tuple[int, int]
    material: str
    verts: List[List[PatchVert]]
    calculatedVerts: List[List[PatchVert]]
    bpy_obj: bpy.types.Object

    def __init__(self, size: Tuple[int, int], material: str) -> None:
        self.size = size
        self.material = material
        self.verts = []
        self.calculatedVerts = None
        self.bpy_obj = None

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

    def Slice(self) -> List[List[List[List[PatchVert]]]]:
        """
        Slice the patch into a 2d list of 3x3 patches to tessellate them later
        """
        if self.size == (3, 3):
            return [[self.verts]]

        res: List[List[List[List[PatchVert]]]] = []
        for i in range(1, self.size[0], 2):
            row = []
            for j in range(1, self.size[1], 2):
                col = [
                    [
                        self.verts[i - 1][j - 1],
                        self.verts[i - 1][j],
                        self.verts[i - 1][j + 1],
                    ],
                    [
                        self.verts[i][j - 1],
                        self.verts[i][j],
                        self.verts[i][j + 1],
                    ],
                    [
                        self.verts[i + 1][j - 1],
                        self.verts[i + 1][j],
                        self.verts[i + 1][j + 1],
                    ],
                ]
                row.append(col)

            res.append(row)

        return res
