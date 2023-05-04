import bpy
from mathutils import Vector
from ..qmap.Patch import PatchVert, Patch
from ..func.Helpers import newPath

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

def create_mesh(patch_data: Patch, entity: int, patchID: int, patchNum: int, tessellationLevel: int, material: str):
    vertices = []
    triangles = []
    # tesselate the patch and create vertices and indices
    vertices = tesselatePatch(patch_data, tessellationLevel)

    for y in range(tessellationLevel):
        for x in range(tessellationLevel):
            i0 = y * (tessellationLevel + 1) + x
            i1 = i0 + 1
            i2 = i0 + (tessellationLevel + 1)
            i3 = i2 + 1

            triangles.append((i0, i2, i1))
            triangles.append((i1, i2, i3))

    # create mesh object and add geometry
    mesh = bpy.data.meshes.new(f"ent_{entity}_patch_{patchID}_{patchNum}_data")
    obj = bpy.data.objects.new(f"ent_{entity}_patch_{patchID}_{patchNum}", mesh)

    # set object location and scene
    bpy.context.scene.collection.objects.link(obj)

    # add vertices and faces to mesh
    mesh.from_pydata([v.pos * 0.0254 for v in vertices], [], triangles)
    uv_layer = mesh.uv_layers.new(name="TextureUV")
    lm_layer = mesh.uv_layers.new(name="LightmapUV")
    lm_layer.active = True
    for loop_index, loop in enumerate(mesh.loops):
        vertex_index = loop.vertex_index
        uv_layer.data[loop_index].uv = vertices[vertex_index].uv
    mesh.update()
    matName = newPath(material)
    if matName in bpy.data.materials:
        material = bpy.data.materials[matName]
        obj.data.materials.append(material)
    return obj

def BuildPatchGeo(patchData: Patch, entity: int, patchID: int, tessellationLevel: int):
    # slice patch into smaller 3x3 patches
    patches = patchData.Slice()
    patchObjs = []
    for i, row in enumerate(patches):
        for j, patch in enumerate(row):
            obj = create_mesh(patch, entity, patchID, (i * len(row)) + j, tessellationLevel, patchData.material)
            obj.select_set(True)
    
    bpy.context.view_layer.objects.active = bpy.context.selected_objects[0]
    bpy.ops.object.join()
    bpy.context.selected_objects[0].name = f"ent_{entity}_patch_{patchID}"
    bpy.ops.object.select_all(action="DESELECT")
