import bpy
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty, IntProperty
from bpy.types import Operator
from mathutils import Vector, Color, Matrix
import bmesh
from math import sqrt, pi
from .qmap.Map import Map
from .qmap.Brush import Brush
from .qmap.Patch import Patch, PatchVert
from .func.Helpers import newPath
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

def binomialCoefficient(n, k):
    coeff = 1
    for i in range(k):
        coeff *= (n - i)
        coeff //= (i + 1)
    return coeff

def evaluateQuadraticBezierPatch(controlPoints, u, v):
    p = PatchVert(Vector((0.0, 0.0, 0.0)), Vector((0.0, 0.0)))

    for i in range(3):
        q = PatchVert(Vector((0.0, 0.0, 0.0)), Vector((0.0, 0.0)))
        for j in range(3):
            q += controlPoints[i][j] * (binomialCoefficient(2, j) * pow(u, j) * pow(1.0 - u, 2 - j))
        p += q * (binomialCoefficient(2, i) * pow(v, i) * pow(1.0 - v, 2 - i))

    return p

def tesselatePatch(controlPoints, tessellationLevel):

    # create a grid of vertices
    vertices = []
    for y in range(tessellationLevel + 1):
        for x in range(tessellationLevel + 1):
            u = float(x) / float(tessellationLevel)
            v = float(y) / float(tessellationLevel)

            p = evaluateQuadraticBezierPatch(controlPoints, u, v)
            vertices.append(p)
    
    return vertices

def create_mesh(patch_data, tessellationLevel):
    vertices = []
    triangles = []
    # tesselate the patch and create vertices and indices
    vertices = tesselatePatch(patch_data.verts, tessellationLevel)

    for y in range(tessellationLevel):
        for x in range(tessellationLevel):
            i0 = y * (tessellationLevel + 1) + x
            i1 = i0 + 1
            i2 = i0 + (tessellationLevel + 1)
            i3 = i2 + 1

            triangles.append((i0, i2, i1))
            triangles.append((i1, i2, i3))

    # create mesh object and add geometry
    mesh = bpy.data.meshes.new("BezierPatch")
    obj = bpy.data.objects.new("BezierPatch", mesh)

    # set object location and scene
    bpy.context.scene.collection.objects.link(obj)

    # add vertices and faces to mesh
    mesh.from_pydata([v.pos * 0.0254 for v in vertices], [], triangles)
    uv_layer = mesh.uv_layers.new()
    for loop_index, loop in enumerate(mesh.loops):
        vertex_index = loop.vertex_index
        uv_layer.data[loop_index].uv = vertices[vertex_index].uv
    mesh.update()
    matName = newPath(patch_data.material)
    if matName in bpy.data.materials:
        material = bpy.data.materials[newPath(patch_data.material)]
        obj.data.materials.append(material)
    return obj

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

    patch_tessellation: IntProperty(
        name="Patch Tessellation Level",
        default=8
    )

    # List of operator properties, the attributes will be assigned
    # to the class instance from the operator settings before calling.

    def execute(self, context):
        mapData = Map.Load(self.filepath)

        # Create a new blank image with 1024x1024 pixels
        lightmap_image = bpy.data.images.new(name="lightmap", width=1024, height=1024, alpha=False)
        pixels = [1.0] * (1024 * 1024 * 4) # Fill with white color
        lightmap_image.pixels = pixels

        extensions = ["tga", "jpg", "png"]

        # Loop through all the materials in mapData.materials
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

            # Create a new material and set it up
            material = bpy.data.materials.new(name=matName)
            material.use_nodes = True
            nodes = material.node_tree.nodes

            for node in nodes:
                nodes.remove(node)

            # Create a texture node for the diffuse image and set its image to the file we found
            tex_node = nodes.new(type="ShaderNodeTexImage")
            tex_node.image = bpy.data.images.load(file)

            # Create a texture node for the lightmap and set its image to the blank image we created earlier
            lightmap_node = nodes.new(type="ShaderNodeTexImage")
            lightmap_node.image = lightmap_image

            # Create a mix shader node to combine the diffuse texture and lightmap
            mix_shader_node = nodes.new(type="ShaderNodeMixShader")
            # mix_shader_node.inputs[0].default_value = 0.5 # Factor

            # Create a diffuse node and an output node
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

                if "target" in entity:
                    targets = mapData.targetnames[entity["target"]]
                    for j, target in enumerate(targets):
                        target_origin = Vector([float(i) for i in target["origin"].split()])
                        direction = origin - target_origin
                        z = direction.normalized()
                        x = Vector((1, 0, 0)).cross(z).normalized()
                        y = direction.cross(x)
                        mat = Matrix((x, y, z)).transposed()
                        angles = mat.to_euler('XYZ')
                        light_data = bpy.data.lights.new(name=f"ent_{i}_data_{j}", type='SPOT')
                        light_obj = bpy.data.objects.new(name=f"ent_{i}_{j}", object_data=light_data)

                        light_obj.location = origin * 0.0254
                        light_obj.rotation_euler = angles
                        light_obj.data.color = color
                        light_obj.data.shadow_soft_size = (energy * pi) * 0.0254
                        light_obj.data.energy = energy * 10

                else:
                    light_data = bpy.data.lights.new(name=f"ent_{i}_data", type='POINT')
                    light_obj = bpy.data.objects.new(name=f"ent_{i}", object_data=light_data)

                    light_obj.location = origin * 0.0254
                    light_obj.data.color = color
                    light_obj.data.shadow_soft_size = (energy * pi) * 0.0254
                    light_obj.data.energy = energy * 10

                bpy.context.scene.collection.objects.link(light_obj)

            if len(entity.geo) != 0:
                for j, geo in enumerate(entity.geo):
                    if isinstance(geo, Brush):
                        geo.CalculateVerts()

                        for k, face in enumerate(geo.faces):
                            if face.material.startswith("common/"):
                                continue

                            mesh_data = bpy.data.meshes.new(f"ent_{i}_geo_{j}_{k}_data")

                            verts = [vert * 0.0254 for vert in face.GetVerts()]
                            idx = [i for i in range(len(verts))]

                            normal = face.GetNormal()

                            mesh_data.from_pydata(verts, [], [idx])
                            for loop in mesh_data.loops:
                                loop.normal = normal

                            mesh_data.update()

                            mesh_obj = bpy.data.objects.new(name=f"ent_{i}_geo_{j}_{k}", object_data=mesh_data)

                            matName = newPath(face.material)
                            if matName in bpy.data.materials:
                                material = bpy.data.materials[newPath(face.material)]
                                mesh_obj.data.materials.append(material)
                                face.texSize = Vector(material.node_tree.nodes["Image Texture"].image.size)

                            face.CalculateUVs()
                            uvs = [Vector((uv.x, -uv.y)) for uv in face.GetUVs()]
                            uv_layer = mesh_data.uv_layers.new(name="TextureUV")
                            lm_layer = mesh_data.uv_layers.new(name="LightmapUV")
                            
                            for loop in mesh_data.loops:
                                vertex_index = loop.vertex_index
                                uv_layer.data[loop.index].uv = uvs[vertex_index]
                            
                            mesh_obj.data.uv_layers.active = uv_layer

                            bpy.context.scene.collection.objects.link(mesh_obj)
                    elif isinstance(geo, Patch):
                        patches = geo.Slice(3)
                        for patch in patches:
                            create_mesh(patch, self.patch_tessellation)


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
