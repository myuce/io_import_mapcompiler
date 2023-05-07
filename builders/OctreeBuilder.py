from mathutils import Vector
from ..qmap.Map import Map
from ..octree.Octree import Node, AABB
from ..func.Helpers import VecMin, VecMax
from typing import Tuple

def GetMapBoundingBox(map: Map) -> AABB:
    map_min, map_max = map.entities[0].geo[0].verts[0], map.entities[0].geo[0].verts[0]

    for entity in map.entities:
        for geo in entity.geo:
            geo_min, geo_max = geo.GetBoundingBox()
            map_min = VecMin(geo_min, map_min)
            map_max = VecMax(geo_max, map_max)

    return map_min, map_max

def BuildeOctree(map: Map) -> Node:
    mapBoundingBox = GetMapBoundingBox(map)
    res = Node(mapBoundingBox)

    for entity in map.entities:
        if len(entity.geo) != 0:
            for geo in entity.geo:
                res.InsertMapObject(geo)
        else:
            if "origin" in entity:
                res.InsertMapObject(entity)

    return res
