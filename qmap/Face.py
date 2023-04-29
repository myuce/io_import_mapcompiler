import bpy
from mathutils import Vector
from copy import copy
from math import atan2, cos, fabs, radians, sin, sqrt, pow
from typing import List, Tuple, Union
from functools import cmp_to_key
from numpy.linalg import solve
from ..func.Helpers import Vec2Str

class BaseUV:
    def __init__(self) -> None:
        pass

    def GetUV(self, vertex: Vector, normal: Vector, texSize: Vector) -> Vector:
        """
        Calculates the UV coordinate of a vertex on a brush face.
        """

        raise NotImplementedError()

class StandardUV(BaseUV):
    """
    Standard texture alignment format used by old Quake games.
    """

    __slots__ = ("xScale", "yScale", "xOffset", "yOffset", "rotation")
    xScale: float
    yScale: float
    xOffset: float
    yOffset: float
    rotation: float

    def GetUV(self, vertex: Vector, normal: Vector, texSize: Vector) -> Vector:
        du: float = fabs(normal.dot(Vector((0, 0, 1))))
        dr: float = fabs(normal.dot(Vector((0, 1, 0))))
        df: float = fabs(normal.dot(Vector((1, 0, 0))))

        uv: Vector = None
        if du >= dr and du >= df:
            uv = Vector((vertex.x, -vertex.y))
        elif dr >= du and dr >= df:
            uv = Vector((vertex.x, -vertex.z))
        elif df >= du and df >= dr:
            uv = Vector((vertex.y, -vertex.z))

        angle: float = radians(self.rotation)
        uv.x = uv.x * cos(angle) - uv.y * sin(angle)
        uv.y = uv.x * sin(angle) + uv.y * cos(angle)
        
        uv.x /= texSize.x
        uv.y /= texSize.y
        uv.x /= self.xScale
        uv.y /= self.yScale
        uv += Vector((self.xOffset / texSize.x, self.yOffset / texSize.y))

        return uv
    
    def __str__(self) -> str:
        return f"{self.xOffset:.6g} {self.yOffset:.6g} {self.rotation:.6g} {self.xScale:.6g} {self.yScale:.6g}"

class ValveUV(BaseUV):
    """
    A relatively newer texture alignment format used by Valve.

    It supports skewing the texture applied on a brush face.
    """

    __slots__ = ("uAxis", "uOffset", "uScale", "vAxis", "vOffset", "vScale")
    uAxis: Vector
    uOffset: float
    uScale: float
    vAxis: Vector
    vOffset: float
    vScale: float

    def GetUV(self, vertex: Vector, normal: Vector, texSize: Vector) -> Vector:
        return Vector((
            vertex.dot(self.uAxis) / (texSize.x * self.uScale) + (self.uOffset / texSize.x),
            vertex.dot(self.vAxis) / (texSize.y * self.vScale) + (self.vOffset / texSize.y))
        )

    def __str__(self) -> str:
        return f"[ {Vec2Str(self.uAxis)} {self.uOffset:.6g} ] [ {Vec2Str(self.vAxis)} {self.vOffset:.6g} ] 0 {self.uScale:.6g} {self.vScale:.6g} 0 0 0"

class Face:
    """
    The class that has all the properties and methods used by a brush face.
    """

    __slots__ = (
        "p1", "p2", "p3", "material", "uvData", "texSize", "vert_idx", "uv_idx", "parent", "bpy_obj",
        "__center__", "__normal__", "__distance__"
    )

    p1: Vector
    p2: Vector
    p3: Vector
    material: str
    uvData: Union[StandardUV, ValveUV]
    texSize: Vector
    vert_idx: List[int]
    uv_idx: List[int]
    parent: 'Brush'
    bpy_obj: bpy.types.Object

    __center__: Vector
    __normal__: Vector
    __distance__: float

    def __init__(self, plane: Tuple[Vector, Vector, Vector], material: str, uvData: Union[StandardUV, ValveUV]) -> None:
        self.vert_idx = []
        self.uv_idx = []
        self.texSize = Vector((512.0, 512.0))
        self.p1, self.p2, self.p3 = plane
        self.material = material
        self.uvData = uvData
        self.parent = None
        self.bpy_obj = None

        self.__center__ = None
        self.__normal__ = None
        self.__distance__ = None

    def __str__(self) -> str:
        return f"( {Vec2Str(self.p1)} ) ( {Vec2Str(self.p2)} ) ( {Vec2Str(self.p3)} ) {self.material} {self.uvData}"

    @staticmethod
    def FromStr(face: str) -> 'Face':
        tok = face.strip().split()
        p1, p2, p3 = Vector([float(i) for i in tok[1:4]]), Vector([float(i) for i in tok[6:9]]), Vector([float(i) for i in tok[11:14]])
        material = tok[15].lower()

        uvData = None
        if tok[16] == "[": # Valve UV format
            uvData = ValveUV()
            uvData.uAxis, uvData.uOffset = Vector([float(i) for i in tok[17:20]]), float(tok[20])
            uvData.vAxis, uvData.vOffset = Vector([float(i) for i in tok[23:26]]), float(tok[26])
            uvData.uScale, uvData.vScale = float(tok[29]), float(tok[30])
        else:
            uvData = StandardUV()
            uvData.xOffset, uvData.yOffset = float(tok[16]), float(tok[17])
            uvData.rotation = float(tok[18])
            uvData.xScale, uvData.yScale = float(tok[19]), float(tok[20])
        
        return Face((p1, p2, p3), material, uvData)


    def AddVert(self, vert: Vector) -> None:
        """
        Adds a vertex to `vert_idx`. The value will be added to the list if it is not a duplicate.
        """

        idx = self.parent.verts.index(vert)
        
        if idx not in self.vert_idx:
            self.vert_idx.append(idx)
    
    def AddUV(self, uv: Vector) -> None:
        """
        Adds a vertex to `uv_idx`. The value will be added to the list if it is not a duplicate.
        """

        self.parent.AddUV(uv)
        idx = self.parent.uvs.index(uv)
        
        self.uv_idx.append(idx)

    def GetVerts(self) -> List[Vector]:
        """
        Returns a list of `Vector` objects referencing the vertices of the brush face.
        """
        return [self.parent.verts[i] for i in self.vert_idx]

    def GetUVs(self) -> List[Vector]:
        """
        Returns a list of `Vector` objects referencing the vertices of the brush face.
        """
        return [self.parent.uvs[i] for i in self.uv_idx]

    def GetNormal(self) -> Vector:
        """
        Calculates the direction where the brush face is facing.
        """

        if self.__normal__ is not None:
            return self.__normal__
        
        ab: Vector = self.p2 - self.p1
        ac: Vector = self.p3 - self.p1
        self.__normal__ = ab.cross(ac).normalized()
        return self.__normal__

    def GetCenter(self) -> Vector:
        """
        Calculates the center of the brush face.
        """

        if len(self.vert_idx) == 0:
            return None
        
        if self.__center__ is not None:
            return self.__center__

        res = Vector((0, 0, 0))

        for vert in self.vert_idx:
            res += self.parent.verts[vert]
        
        res /= len(self.vert_idx)
        self.__center__ = res
        return res
    
    def GetDistance(self) -> float:
        normal: Vector = self.GetNormal()
        return ((self.p1.x * normal.x) + (self.p1.y * normal.y) + (self.p1.z * normal.z)) / sqrt(pow(normal.x, 2) + pow(normal.y, 2) + pow(normal.z, 2))
    
    def SortVertices(self) -> None:
        """
        Sorts vertices clockwise.
        """

        center: Vector = self.GetCenter()

        if center is None:
            print(f"Can't find the center of brush {self.p1} {self.p2} {self.p3}. Skipping...")

        normal: Vector = self.GetNormal()

        def compare(_a: int, _b: int):
            a = self.parent.verts[_a]
            b = self.parent.verts[_b]
            ca: Vector = center - a
            cb: Vector = center - b
            caXcb: Vector = ca.cross(cb)
            if normal.dot(caXcb) > 0:
                return 1
            return -1
        
        self.vert_idx.sort(key=cmp_to_key(compare))

    def CalculateUVs(self) -> None:
        normal = self.GetNormal()

        for idx in self.vert_idx:
            self.AddUV(self.uvData.GetUV(self.parent.verts[idx], normal, self.texSize))

    def Triangulate(self, return_idx=False) -> List[Tuple[Vector, Vector]]:
        verts = self.vert_idx if return_idx else self.GetVerts()
        uvs = self.uv_idx if return_idx else self.GetUVs()

        res: List[Tuple[Tuple[Vector, Vector], Tuple[Vector, Vector], Tuple[Vector, Vector]]] = []
        numVerts = len(verts)

        res.append((
            (verts[0], uvs[0]),
            (verts[numVerts - 1], uvs[numVerts - 1]),
            (verts[1], uvs[1])
        ))

        for i in range(int(numVerts / 2)):
            res.append((
                (verts[i], uvs[i]),
                (verts[numVerts - i], uvs[numVerts - i]),
                (verts[i + 1], uvs[i + 1])
            ))

            res.append((
                (verts[numVerts - i], uvs[numVerts - i]),
                (verts[numVerts - i - 1], uvs[numVerts - i - 1]),
                (verts[i + 1], uvs[i + 1])
            ))

        return res

    @staticmethod
    def FromPoints(p1: Vector, p2: Vector, p3: Vector):
        """
        Returns a `Face` object using the points given.

        Apart from the plane points, all the other properties are set to `None`. 
        """
        
        res = Face()
        res.p1, res.p2, res.p3 = p1, p2, p3
        res.material = res.uvData = None
        return res

from .Brush import Brush
