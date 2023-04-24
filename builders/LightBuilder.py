from math import pi
import bpy
from mathutils import Vector, Color, Matrix
from ..qmap.Map import Map
from ..qmap.Entity import Entity

def BuildLight(light: Entity, entity: int, mapData: Map):
    origin = Vector([float(i) for i in light["origin"].split()]) if "origin" in light else Vector((0, 0, 0))
    color = Color([float(i) for i in light["_color"].split()]) if "_color" in light else Color((1, 1, 1))
    energy = float(light["light"]) if "light" in light else 300.0

    if "target" in light:
        targets = mapData.targetnames[light["target"]]
        for i, target in enumerate(targets):
            target_origin = Vector([float(i) for i in target["origin"].split()])
            direction = origin - target_origin
            z = direction.normalized()
            x = Vector((1, 0, 0)).cross(z).normalized()
            y = direction.cross(x)
            mat = Matrix((x, y, z)).transposed()
            angles = mat.to_euler('XYZ')
            light_data = bpy.data.lights.new(name=f"ent_{entity}_data_{i}", type='SPOT')
            light_obj = bpy.data.objects.new(name=f"ent_{entity}_{i}", object_data=light_data)

            light_obj.location = origin * 0.0254
            light_obj.rotation_euler = angles
            light_obj.data.color = color
            light_obj.data.shadow_soft_size = (energy * pi) * 0.0254
            light_obj.data.energy = energy * 10

    else:
        light_data = bpy.data.lights.new(name=f"ent_{entity}_data", type='POINT')
        light_obj = bpy.data.objects.new(name=f"ent_{entity}", object_data=light_data)

        light_obj.location = origin * 0.0254
        light_obj.data.color = color
        light_obj.data.shadow_soft_size = (energy * pi) * 0.0254
        light_obj.data.energy = energy * 10

    bpy.context.scene.collection.objects.link(light_obj)
