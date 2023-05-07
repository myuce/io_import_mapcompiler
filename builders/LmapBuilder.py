import bpy

def BuildLightmapUVs(lightmap_size: int=1024) -> None:
    # deselect all the objects first
    bpy.ops.object.select_all(action="DESELECT")

    # select all mesh objects generated from map data
    for object in bpy.data.objects:
        if object.type == "MESH" and object.name.startswith("ent_"):
            object.select_set(True)

    bpy.context.view_layer.objects.active = bpy.context.selected_objects[0]
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.uv.lightmap_pack(PREF_IMG_PX_SIZE=lightmap_size, PREF_MARGIN_DIV=1.0, PREF_PACK_IN_ONE=True)
    bpy.ops.object.mode_set(mode='OBJECT')

def CreateLightmapImage(width, height) -> None:
    image = bpy.data.images.new(name="LightmapImage", width=width, height=height)
    pixels = [1.0] * (width * height * 4)
    image.pixels = pixels
    return image

def BakeLightmap():
    bpy.data.scenes["Scene"].render.engine = "CYCLES"
    bpy.context.scene.cycles.device = 'CPU'
    bpy.context.scene.cycles.bake_type = 'DIFFUSE'
    bpy.context.scene.cycles.samples = 64
    bpy.context.scene.cycles.margin = 1
    bpy.context.scene.render.bake.use_pass_direct = True
    bpy.context.scene.render.bake.use_pass_indirect = True
    bpy.context.scene.render.bake.use_pass_color = False

    bpy.ops.object.bake(type="DIFFUSE")

    bpy.ops.object.select_all(action="DESELECT")

def GetLightmapPixels():
    image = bpy.data.images["LightmapImage"]
    pixels = []
    for i in range(0, len(image.pixels), 4):
        pixels.append(int(image.pixels[i] * 255))
        pixels.append(int(image.pixels[i] * 255))
        pixels.append(int(image.pixels[i] * 255))
    
    return pixels
