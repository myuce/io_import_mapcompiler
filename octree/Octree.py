from mathutils import Vector
from typing import List, Tuple, Union
from collections import namedtuple
from ..qmap.Brush import Brush
from ..qmap.Entity import Entity
from ..func.Helpers import Str2Vec

AABB = Tuple[Vector, Vector]

class Node:
    __slots__ = ("boundingBox", "parent", "objects", "children")

    boundingBox: AABB
    parent: 'Node'
    objects: List[Tuple[int, ...]]
    children: List['Node']

    def __init__(self, boundingBox, parent=True):
        self.boundingBox = boundingBox
        self.objects = [] if not parent else None
        self.children = [] if parent else None

        if parent:
            self.CreateChildren()

    def CreateChildren(self):
        min, max = self.boundingBox
        center = (min + max) / 2
        extents = max - center

        isParent = extents.x <= 128 or extents.y <= 128 or extents.z <= 128
        offsets = [
            Vector(0, 0, -1),
            Vector(0, 1, -1),
            Vector(1, 0, -1),
            Vector(1, 1, -1),
            Vector(0, 0, 0),
            Vector(0, 1, 0),
            Vector(1, 0, 0),
            Vector(1, 1, 0)
        ]

        for offset in offsets:
            min_point = center + extents * offset
            max_point = min_point + extents
            self.children.append(Node((min_point, max_point), isParent))

    def CollidesWithBrush(self, brush: Brush):
        brushAABB = brush.GetBoundingBox()
        return (
            (self.boundingBox[0].x <= brushAABB[1].x and self.boundingBox[1].x >= brushAABB[0].x) and
            (self.boundingBox[0].y <= brushAABB[1].y and self.boundingBox[1].y >= brushAABB[0].y) and
            (self.boundingBox[0].z <= brushAABB[1].z and self.boundingBox[1].z >= brushAABB[0].z)
        )

    def CollidesWithEntity(self, entity: Entity):
        if entity.boundingBox is not None:
            return (
                (self.boundingBox[0].x <= entity.boundingBox[1].x and self.boundingBox[1].x >= entity.boundingBox[0].x) and
                (self.boundingBox[0].y <= entity.boundingBox[1].y and self.boundingBox[1].y >= entity.boundingBox[0].y) and
                (self.boundingBox[0].z <= entity.boundingBox[1].z and self.boundingBox[1].z >= entity.boundingBox[0].z)
            )
        
        origin = Str2Vec(entity["origin"])

        return (
            origin.x >= self.boundingBox[0].x and origin.x <= self.boundingBox[1].x and
            origin.y >= self.boundingBox[0].y and origin.y <= self.boundingBox[1].y and
            origin.z >= self.boundingBox[0].z and origin.z <= self.boundingBox[1].z
        )

    def AddObject(self, obj: Union[Entity, Brush]):
        if obj not in self.objects:
            self.objects.append(obj.id)

    def InsertMapObject(self, obj: Union[Brush, Entity]):
        collidesWith = self.CollidesWithBrush if isinstance(obj, Brush) else self.CollidesWithEntity

        if collidesWith(obj):
            if self.objects is not None:
                self.AddObject(obj)
            else:
                for child in self.children:
                    child.InsertMapObject(obj)
