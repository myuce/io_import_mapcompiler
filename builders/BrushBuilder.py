import bpy
from mathutils import Vector
from ..qmap.Brush import Brush
from ..qmap.Face import Face
from ..func.Helpers import newPath

def BuildBrushGeo(brush: Brush, entity: int, brushID: int):
    brush.CalculateVerts()

    for i, face in enumerate(brush.faces):
        if face.material.startswith("common/"):
            continue

        mesh_data = bpy.data.meshes.new(f"ent_{entity}_brush_{brushID}_face_{i}_data")

        verts = [vert * 0.0254 for vert in face.GetVerts()]
        idx = [i for i in range(len(verts))]

        normal = face.GetNormal()

        mesh_data.from_pydata(verts, [], [idx])
        for loop in mesh_data.loops:
            loop.normal = normal
        
        mesh_data.update()

        mesh_obj = bpy.data.objects.new(name=f"ent_{entity}_brush_{brushID}_face_{i}", object_data=mesh_data)
        
        matName = newPath(face.material)
        if matName in bpy.data.materials:
            material = bpy.data.materials[newPath(face.material)]
            mesh_obj.data.materials.append(material)
            face.texSize = Vector(material.node_tree.nodes["Image Texture"].image.size)

        face.CalculateUVs()
        uvs = [Vector((uv.x, -uv.y)) for uv in face.GetUVs()]
        uv_layer = mesh_data.uv_layers.new(name="TextureUV")
        lm_layer = mesh_data.uv_layers.new(name="LightmapUV")
        lm_layer.active = True
        
        for loop in mesh_data.loops:
            vertex_index = loop.vertex_index
            uv_layer.data[loop.index].uv = uvs[vertex_index]
        
        bpy.context.scene.collection.objects.link(mesh_obj)

        face.lm = mesh_data.uv_layers["LightmapUV"].data
