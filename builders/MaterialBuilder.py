import bpy
import os
from ..qmap.Map import Map
from ..func.Helpers import newPath

def BuildMaterials(mapData: Map, game_path: str):
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
            if os.path.exists(f"{game_path}/textures/{material}.{ext}"):
                file = f"{game_path}/textures/{material}.{ext}"
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