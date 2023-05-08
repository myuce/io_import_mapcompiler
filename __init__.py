import bpy
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty, IntProperty
from bpy.types import Operator
from .qmap.Map import Map, Brush, Patch
from .builders.MaterialBuilder import BuildMaterials
from .builders.BrushBuilder import BuildBrushGeo
from .builders.PatchBuilder import BuildPatchGeo
from .builders.LightBuilder import BuildLight
from .builders.LmapBuilder import BuildLightmapUVs, BakeLightmap
from .builders.LevelBuilder import BuildLevel

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
    bl_idname = "import_quake.map_data"
    bl_label = "Import Quake Map"

    # ImportHelper mixin class uses this
    filename_ext = ".map"

    filter_glob: StringProperty(
        default="*.map",
        options={'HIDDEN'},
        maxlen=1024
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

    bake_lightmaps: BoolProperty(
        name="Bake Lightmaps",
        default=False
    )

    lightmap_size: EnumProperty(
        items=(
            ("512", "512x512", "512x512"),
            ("1024", "1024x1024", "1024x1024"),
            ("2048", "2048x2048", "2048x2048"),
            ("4096", "4096x4096", "4096x4096")
        ),
        name="Lightmap Image Size",
        default="1024"
    )

    save_level: BoolProperty(
        name="Compile",
        default=False
    )

    def execute(self, context):
        mapData = Map.Load(self.filepath)

        BuildMaterials(mapData, self.game_path)

        for i, entity in enumerate(mapData.entities):
            classname = entity["classname"]

            if classname == "light":
                BuildLight(entity, i, mapData)
                continue

            if len(entity.geo) != 0:
                for j, geo in enumerate(entity.geo):
                    if isinstance(geo, Brush):
                        BuildBrushGeo(geo, i, j)
                    elif isinstance(geo, Patch):
                        continue
                        # BuildPatchGeo(geo, i, j, self.patch_tessellation)

        BuildLightmapUVs(int(self.lightmap_size))

        if self.bake_lightmaps:
            BakeLightmap()
        
        if self.save_level:
            BuildLevel(self.filepath, mapData)

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
