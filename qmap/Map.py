from enum import Enum
from mathutils import Vector
from typing import Any, Dict, List
from .Entity import Entity
from .Brush import Brush
from .Face import Face
from .Patch import Patch, PatchVert

def Error(char, line):
    raise Exception(f"Unexpected '{char}' on line {line}. Stopping...")

class Mode(Enum):
    NONE = 0
    Entity = 1
    Brush = 2
    Curve = 3

class Map:
    __slots__ = ("settings", "entities", "materials", "matSizes", "models", "modelMaterials", "modelData", "modelMaterialData", "targets", "targetnames")
    settings: dict
    entities: List[Entity]
    materials: List[str]
    matSizes: Dict[str, Vector]
    models: List[str]
    modelMaterials: List[str]
    modelData: Dict[str, str]
    modelMaterialData: Dict[str, Any]
    targets: Dict[str, List[Entity]]
    targetnames: Dict[str, List[Entity]]

    def __init__(self) -> None:
        self.settings = {}
        self.entities = []
        self.materials = []
        self.matSizes = {}
        self.models = []
        self.modelMaterials = []
        self.modelData = {}
        self.modelMaterialData = {}
        self.targets = {}
        self.targetnames = {}

    def __str__(self) -> str:
        res = ""

        for entity in self.entities:
            res += str(entity)
    
        return res
    
    def AddMaterial(self, material: str):
        material = material.lower().strip()
        if material not in self.materials:
            self.materials.append(material)

    def AddModel(self, model: str):
        model = model.lower()
        if model not in self.models:
            self.models.append(model)

    def Save(self):
        raise NotImplementedError()

    def ProcessGeo(self) -> None:
        for entity in self.entities:
            for geo in entity.geo:
                if isinstance(geo, Brush):
                    geo.CalculateVerts()
                    geo.CalculateUVs()

    def AddTarget(self, target, entity):
        if target not in self.targets:
            self.targets[target] = []
        
        self.targets[target].append(entity)


    def AddTargetName(self, targetname, entity):
        if targetname not in self.targetnames:
            self.targetnames[targetname] = []
        
        self.targetnames[targetname].append(entity)

    @staticmethod
    def Load(path: str) -> 'Map':
        res = Map()

        with open(path, "r") as file:
            mode = Mode.NONE
            lines = file.readlines()

            for i, line in enumerate(lines):
                line = line.strip()
                
                if line.startswith("//") or line == "":
                    continue # skip comments

                elif line == "{":
                    if mode == Mode.NONE:
                        mode = Mode.Entity
                        res.entities.append(Entity(len(res.entities)))
                        continue

                    elif mode == Mode.Entity:
                        if lines[i + 1].startswith("("):
                            mode = Mode.Brush
                            res.entities[-1].geo.append(Brush(len(res.entities[-1].geo), res.entities[-1].id))
                            continue

                        elif lines[i + 1].strip() == "patchDef2":
                            mode = Mode.Curve
                            material = lines[i + 3].strip()
                            size = tuple([int(i) for i in lines[i + 4].split()[1:3]])
                            res.entities[-1].geo.append(Patch(size, material))
                            res.AddMaterial(material)
                            continue

                    elif mode == Mode.Curve and lines[i - 1].strip() == "patchDef2":
                        continue
                    
                    else:
                        Error("{", i + 1)
                
                elif line == "}":
                    if mode == Mode.Brush:
                        mode = Mode.Entity
                        continue
                    if mode == Mode.Curve:
                        prev = lines[i - 1].strip()
                        if prev == "}":
                            mode = Mode.Entity
                            continue
                        elif prev == ")":
                            continue
                    elif mode == Mode.Entity:
                        mode = Mode.NONE
                        continue
                    else:
                        Error("}", i + 1)

                elif line[0] == '"':
                    if mode == Mode.Entity:
                        key, value = Entity.ParseKVP(line)
                        res.entities[-1][key] = value

                        if key == "targetname":
                            res.AddTargetName(value, res.entities[-1])
                        if key == "target":
                            res.AddTarget(value, res.entities[-1])
                    else:
                        Error('"', i + 1)

                elif line == "(":
                    if mode == Mode.Curve:
                        continue
                    else:
                        Error("(", i + 1)

                elif line == ")":
                    if mode == Mode.Curve:
                        continue
                    else:
                        Error(")", i + 1)

                elif line.startswith("( ("):
                    if mode == Mode.Curve:
                        res.entities[-1].geo[-1].verts.append(PatchVert.FromStr(line))
                        continue
                    else:
                        Error("(", i + 1)

                elif line.startswith("("):
                    if mode == Mode.Brush:
                        face = Face.FromStr(line)
                        res.entities[-1].geo[-1].AddFace(face)
                        res.AddMaterial(face.material)
                        continue

                    elif mode == Mode.Curve:
                        continue

                    else:
                        Error("(", i + 1)

                elif line == "patchDef2":
                    if mode == Mode.Curve:
                        continue
                    else:
                        Error("patchDef2", i + 1)
                else:
                    if lines[i - 2].strip() != "patchDef2":
                        Error(line.strip(), i + 1)

        return res
