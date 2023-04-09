from mathutils import Vector

def Vec2Str(vec):
    return " ".join([f"{v:5g}" for v in vec])

def Str2Vec(string: str):
    return Vector([float(i) for i in string.split()])