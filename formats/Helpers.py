from mathutils import Vector

def Vec2Str(vec):
    return " ".join([f"{v:5g}" for v in vec])

def Str2Vec(string: str):
    return Vector([float(i) for i in string.split()])

from pathlib import Path
from os.path import basename, splitext, dirname
from hashlib import shake_256

def shortenName(name: str, length=13):
    name = splitext(basename(name).strip())[0]
    return name[:length] + name[-length:] if len(name) > (length * 2) else name

def shortenPath(path: str, dig=4):
    return shake_256(path.encode()).hexdigest(dig)

def newPath(path: str, shorten=False, prefix=""):
    path = f"{prefix}/" + Path(path).as_posix().strip().lower().replace("{", "_").replace("}", "_").replace("(", "_").replace(")", "_").replace(" ", "_")
    fileName = basename(path)
    if shorten:
        fileName = shortenName(fileName)
    dirName = dirname(path)
    return f"{shortenPath(dirName)}_{fileName}"