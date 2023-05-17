import bpy

def BuildLightmapUVs(lightmap_size=(1024, 1024)) -> None:
    # deselect all the objects first
    bpy.ops.object.select_all(action="DESELECT")

    # select all mesh objects generated from map data
    for object in bpy.data.objects:
        if object.type == "MESH" and object.name.startswith("ent_"):
            object.select_set(True)

    bpy.context.view_layer.objects.active = bpy.context.selected_objects[0]
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.uv.lightmap_pack(PREF_IMG_PX_SIZE=lightmap_size[0], PREF_MARGIN_DIV=1.0, PREF_PACK_IN_ONE=True)
    bpy.ops.object.mode_set(mode='OBJECT')

def CreateLightmapImage(width, height) -> None:
    image = bpy.data.images.new(name="LightmapImage", width=width, height=height)
    pixels = [1.0] * (width * height * 4)
    image.pixels = pixels

    return image

def BakeLightmap():
    bpy.data.scenes["Scene"].render.engine = "CYCLES"
    bpy.data.scenes["Scene"].cycles.device= "GPU"
    bpy.data.scenes["Scene"].cycles.bake_type = "DIFFUSE"
    bpy.data.scenes["Scene"].cycles.samples = 64
    bpy.data.scenes["Scene"].render.bake.margin = 1
    bpy.data.scenes["Scene"].render.bake.use_pass_direct = True
    bpy.data.scenes["Scene"].render.bake.use_pass_indirect = True
    bpy.data.scenes["Scene"].render.bake.use_pass_color = False

    bpy.data.scenes["Scene"].cycles.max_bounces = 12
    bpy.data.scenes["Scene"].cycles.diffuse_bounces = 4
    bpy.data.scenes["Scene"].cycles.glossy_bounces = 0
    bpy.data.scenes["Scene"].cycles.transmission_bounces = 0
    bpy.data.scenes["Scene"].cycles.volume_bounces = 0
    bpy.data.scenes["Scene"].cycles.transparent_max_bounces = 0

    bpy.ops.object.bake(type="DIFFUSE")

    bpy.ops.object.select_all(action="DESELECT")

    # denoise the lightmap image
    bpy.data.scenes["Scene"].use_nodes = True
    nodes = bpy.data.scenes["Scene"].node_tree.nodes
    links = bpy.data.scenes["Scene"].node_tree.links

    for node in nodes:
        nodes.remove(node)

    new_lightmap_image = nodes.new(type="CompositorNodeImage")
    denoise = nodes.new(type="CompositorNodeDenoise")
    despeckle = nodes.new(type="CompositorNodeDespeckle")
    composite = nodes.new(type="CompositorNodeComposite")
    viewer = nodes.new(type="CompositorNodeViewer")

    new_lightmap_image.image = bpy.data.images["LightmapImage"]  # assign image here

    links.new(new_lightmap_image.outputs["Image"], denoise.inputs["Image"])
    links.new(denoise.outputs["Image"], despeckle.inputs["Image"])
    links.new(despeckle.outputs["Image"], viewer.inputs["Image"])
    links.new(despeckle.outputs["Image"], composite.inputs["Image"])

    new_lightmap_image.select = True
    nodes.active = new_lightmap_image

def GetLightmapData():
    image = bpy.data.images["LightmapImage"]
    pixels = bytearray([int(p * 255) for i, p in enumerate(image.pixels) if (i + 1) % 4 != 0])
    
    return image, pixels
