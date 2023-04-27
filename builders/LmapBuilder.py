import bpy

def BuildLightmapUVs() -> None:
    # deselect all the objects first
    bpy.ops.object.select_all(action="DESELECT")

    # select all mesh objects generated from map data
    for object in bpy.data.objects:
        if object.type == "MESH" and object.name.startswith("ent_"):
            object.select_set(True)

    bpy.context.view_layer.objects.active = bpy.context.selected_objects[0]
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.uv.lightmap_pack(PREF_IMG_PX_SIZE=1024)
    bpy.ops.object.mode_set(mode='OBJECT')