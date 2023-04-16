import bpy
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty
from bpy.types import Operator
from mathutils import Vector, Color
import bmesh
from math import sqrt
from .formats.Map import Map
from .formats.Brush import Brush
from .formats.Patch import Patch
from .formats.Helpers import newPath
import os

bl_info = {
    "name": "mapcompiler",
    "author": "johndoe",
    "version": (0, 0, 1),
    "blender": (3, 5, 0),
    "location": "File > Import-Export > Import Quake map",
    "description": "Map compiler for johndoe's engine",
    "category": "Import-Export"
}

class ImportMap(Operator, ImportHelper):
    """This appears in the tooltip of the operator and in the generated docs"""
    bl_idname = "import_quake.map_data"  # important since its how bpy.ops.import_test.some_data is constructed
    bl_label = "Import Quake Map"

    # ImportHelper mixin class uses this
    filename_ext = ".map"

    filter_glob: StringProperty(
        default="*.map",
        options={'HIDDEN'},
        maxlen=1024,  # Max internal buffer length, longer would be clamped.
    )

    game_path: StringProperty(
        name="Game Path",
        default="C:/stuff/games/other/q3a/baseq3",
        maxlen=1024
    )

    # List of operator properties, the attributes will be assigned
    # to the class instance from the operator settings before calling.

    def execute(self, context):
        mapData = Map.Load(self.filepath)

        extensions = ["tga", "jpg", "png"]
        for material in mapData.materials:
            matName = newPath(material)
            file = None
            for ext in extensions:
                if os.path.exists(f"{self.game_path}/textures/{material}.{ext}"):
                    file = f"{self.game_path}/textures/{material}.{ext}"
                    break
            
            if file is None:
                print(f"Can't find material {material}")
                continue
            
            material = bpy.data.materials.new(name=matName)
            material.use_nodes = True
            nodes = material.node_tree.nodes

            for node in nodes:
                nodes.remove(node)

            tex_node = nodes.new(type="ShaderNodeTexImage")
            tex_node.image = bpy.data.images.load(file)
            diffuse_node = nodes.new(type="ShaderNodeBsdfDiffuse")
            output_node = nodes.new(type="ShaderNodeOutputMaterial")
            links = material.node_tree.links
            links.new(tex_node.outputs["Color"], diffuse_node.inputs["Color"])
            links.new(diffuse_node.outputs["BSDF"], output_node.inputs["Surface"])

        for i, entity in enumerate(mapData.entities):
            classname = entity["classname"]

            if classname == "light":
                origin = Vector([float(i) for i in entity["origin"].split()]) if "origin" in entity else Vector((0, 0, 0))
                color = Color([float(i) for i in entity["_color"].split()]) if "_color" in entity else Color((1, 1, 1))
                energy = float(entity["light"]) if "light" in entity else 300.0
                radius = float(entity["radius"]) if "radius" in entity else 64.0

                light_data = bpy.data.lights.new(name=f"{classname}_data_{i}", type='POINT')
                light_obj = bpy.data.objects.new(name=f"{classname}_{i}", object_data=light_data)

                light_obj.location = origin  * 0.0254
                light_obj.data.color = color
                light_obj.data.shadow_soft_size = radius * 0.0254
                light_obj.data.energy = energy * 0.019683

                bpy.context.scene.collection.objects.link(light_obj)

            if len(entity.geo) != 0:
                for j, geo in enumerate(entity.geo):
                    if isinstance(geo, Brush):
                        geo.CalculateVerts()

                        for k, face in enumerate(geo.faces):
                            mesh_data = bpy.data.meshes.new(f"{classname}_{i}_geo_{j}_{k}_data")

                            verts = [vert * 0.0254 for vert in face.GetVerts()]
                            idx = [i for i in range(len(verts))]

                            normal = face.GetNormal()

                            mesh_data.from_pydata(verts, [], [idx])
                            for loop in mesh_data.loops:
                                loop.normal = normal

                            mesh_data.update()

                            mesh_obj = bpy.data.objects.new(name=f"{classname}_{i}_geo_{j}_{k}", object_data=mesh_data)

                            matName = newPath(face.material)
                            if matName in bpy.data.materials:
                                material = bpy.data.materials[newPath(face.material)]
                                mesh_obj.data.materials.append(material)
                                face.texSize = Vector(material.node_tree.nodes["Image Texture"].image.size)

                            face.CalculateUVs()
                            face.CalculateLightmapUVs()
                            uvs = [Vector((uv.x, -uv.y)) for uv in face.GetUVs()]
                            lightmap_uvs = [Vector((uv.x, -uv.y)) for uv in face.lightmapUVs]
                            uv_layer = mesh_data.uv_layers.new(name="TextureUV")
                            lm_layer = mesh_data.uv_layers.new(name="LightmapUV")
                            
                            for loop in mesh_data.loops:
                                vertex_index = loop.vertex_index
                                uv_layer.data[loop.index].uv = uvs[vertex_index]
                                lm_layer.data[loop.index].uv = lightmap_uvs[vertex_index]
                            
                            mesh_obj.data.uv_layers.active = uv_layer

                            bpy.context.scene.collection.objects.link(mesh_obj)
                    elif isinstance(geo, Patch):
                        pass


        return {'FINISHED'}


def menu_func_import(self, context):
    self.layout.operator(ImportMap.bl_idname, text="Import Quake Map")


def register():
    bpy.utils.register_class(ImportMap)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)


def unregister():
    bpy.utils.unregister_class(ImportMap)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)


if __name__ == "__main__":
    register()

    bpy.ops.import_test.some_data('INVOKE_DEFAULT')
