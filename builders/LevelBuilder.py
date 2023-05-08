from os import remove
from os.path import splitext, basename, dirname, exists
from struct import pack
from ..qmap.Map import Map
from .LmapBuilder import GetLightmapData
from .OctreeBuilder import GetMapBoundingBox, Node

H = "16s" # header length
KV = "128s" # key/value length
M = "256s" # material name length

def BuildLevel(mapPath: str, mapData: Map):
    mapDir = dirname(mapPath)
    mapName = basename(mapPath)
    mapName, _ = splitext(mapName)
    lvlFile = f"{mapDir}/{mapName}.lvl"

    octree = Node(GetMapBoundingBox(mapData), True)

    if exists(lvlFile):
        remove(lvlFile)
    
    with open(lvlFile, "wb") as file:
        write = lambda size, *data: file.write(pack(size, *data))
        # level header
        write(H, b"JDLEVEL")

        # material data
        write(H, b"MATERIALS")
        write("i", len(mapData.materials))

        for mat in mapData.materials:
            write(M, bytes(mat, "ASCII"))

        mat_idx = {matname: idx for idx, matname in enumerate(mapData.materials)}

        # lightmap image data
        lmap_image, lmap_pixels = GetLightmapData()
        write(H, b"LIGHTMAP")
        write("2i", *lmap_image.size)
        file.write(lmap_pixels)

        # entity header & num entities
        write(H, b"ENTITY")
        write("i", len(mapData.entities))

        # write entity data
        for entity in mapData.entities:
            # entity bounding box. only point entities need it.
            if entity.boundingBox is not None:
                write("6f", *entity.boundingBox[0], *entity.boundingBox[1])
            else:
                write("6f", *([0.0] * 6))

            write("i", len(entity.properties)) # num key/values
            write("i", len(entity.geo)) # number of brushes. should be 0 for point entities like models, lights etc.
            for key, value in entity.properties.items():
                write(KV, bytes(key, "ASCII"))
                write(KV, bytes(value, "ASCII"))

            if len(entity.geo) == 0:
                continue

            for brush in entity.geo:
                # bounding box
                min, max = brush.GetBoundingBox()
                write("3f", *min)
                write("3f", *max)
                # write vertices
                write("i", len(brush.verts)) # num verts
                for vert in brush.verts:
                    write("3f", *vert)
                
                # write uvs
                write("i", len(brush.uvs)) #num uvs
                for uv in brush.uvs:
                    write("2f", *uv)
                
                # write faces
                write("i", len(brush.faces)) #num faces
                for face in brush.faces:
                    write("i", mat_idx[face.material]) # material index

                    # face vert indices
                    write("i", len(face.vert_idx)) # num verts
                    for vert in face.vert_idx:
                        write("i", vert)
                    
                    # face uv indices
                    write("i", len(face.uv_idx)) # num uvs
                    for uv in face.uv_idx:
                        write("i", uv)

                    # lightmap uvs
                    write("i", len(face.lm))
                    for lm in face.lm:
                        write("2f", *lm) # lightmap uvs are kept as vectors, not indices
