import bpy
import os
from ..qmap.Map import Map
from ..func.Helpers import newPath
from .LmapBuilder import CreateLightmapImage

# material with checker texture used by objects with no material to be found
def CreateDefaultMaterial():
        # Create a new material and set it up
        material = bpy.data.materials.new(name="404")
        material.use_nodes = True
        nodes = material.node_tree.nodes

        for node in nodes:
            nodes.remove(node)

        # Create a texture node for the diffuse image and set its image to the file we found
        tex_node = nodes.new(type="ShaderNodeTexChecker")

        # Create a diffuse node and an output node
        diffuse_node = nodes.new(type="ShaderNodeBsdfDiffuse")
        output_node = nodes.new(type="ShaderNodeOutputMaterial")
        links = material.node_tree.links
        links.new(tex_node.outputs["Color"], diffuse_node.inputs["Color"])
        links.new(diffuse_node.outputs["BSDF"], output_node.inputs["Surface"])

        # Create a texture node for the lightmap and set its image to the blank image we created earlier
        lightmap_node = nodes.new(type="ShaderNodeTexImage")
        lightmap_node.image = bpy.data.images["LightmapImage"]

        # create a uv map node and set its uv layer
        uv_node = nodes.new(type="ShaderNodeUVMap")
        uv_node.uv_map = "LightmapUV"

        # link the lightmap image and the uv node
        links.new(uv_node.outputs["UV"], lightmap_node.inputs["Vector"])

        # set the lightmap image as the active node
        nodes.active = lightmap_node

def BuildMaterials(mapData: Map, game_path: str, lightmapImageSize=(1024, 1024)):
    lightmapImage = CreateLightmapImage(*lightmapImageSize)
    CreateDefaultMaterial()

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

        # Create a diffuse node and an output node
        diffuse_node = nodes.new(type="ShaderNodeBsdfDiffuse")
        output_node = nodes.new(type="ShaderNodeOutputMaterial")
        links = material.node_tree.links
        links.new(tex_node.outputs["Color"], diffuse_node.inputs["Color"])
        links.new(diffuse_node.outputs["BSDF"], output_node.inputs["Surface"])

        # Create a texture node for the lightmap and set its image to the blank image we created earlier
        lmap_img_node = nodes.new(type="ShaderNodeTexImage")
        lmap_img_node.image = lightmapImage

        # create a uv map node and set its uv layer
        uv_node = nodes.new(type="ShaderNodeUVMap")
        uv_node.uv_map = "LightmapUV"

        # link the lightmap image and the uv node
        links.new(uv_node.outputs["UV"], lmap_img_node.inputs["Vector"])

        # set the lightmap image as the active node
        nodes.active = lmap_img_node

        # create a shader for lightmap
        lmap_diffuse_node = nodes.new(type="ShaderNodeBsdfDiffuse")
        lmap_output_node = nodes.new(type="ShaderNodeOutputMaterial")
        links.new(lmap_img_node.outputs["Color"], lmap_diffuse_node.inputs["Color"])
        links.new(lmap_diffuse_node.outputs["BSDF"], lmap_output_node.inputs["Surface"])

        # create mix shader to mix diffuse and lightmap
        mix_node = nodes.new(type="ShaderNodeMixShader")
        mix_output_node = nodes.new(type="ShaderNodeOutputMaterial")

        links.new(mix_output_node.inputs["Surface"], mix_node.outputs["Shader"])
        links.new(mix_node.inputs[1], diffuse_node.outputs["BSDF"])
        links.new(mix_node.inputs[2], lmap_diffuse_node.outputs["BSDF"])
