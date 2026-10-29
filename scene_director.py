#!/usr/bin/env python3
"""Director determinista de escenas para HEC REELS.

No usa IA ni servicios externos. Reconoce categorías limitadas y conserva
los tiempos exactos del audio Piper; jamás ejecuta código del texto del usuario.
"""
import argparse
import json
import re
import unicodedata
from pathlib import Path

CATEGORIES = {
    "payment": ("terminal", "tarjeta", "tarjetas", "banco", "bancaria", "pago", "pagos", "cobro", "cobrar", "tpv", "pos", "contactless"),
    "network": ("internet", "router", "wifi", "red", "redes", "dns", "servidor", "paquete", "ip", "conexion", "conectar", "datos"),
    "food": ("pasta", "comida", "cocina", "restaurante", "ensalada", "pizza", "hamburguesa", "alimento", "plato"),
    "motorcycle": ("moto", "motocicleta", "llanta", "motor", "casco", "motociclista"),
    "cloud": ("nube", "cloud", "servidores", "computo", "almacenamiento", "firebase", "aws", "azure", "googlecloud"),
    "generic": (),
}
LABELS = {
    "payment":"Terminal y pago",
    "network":"Red y conexiones",
    "food":"Plato y alimentos",
    "motorcycle":"Motocicleta",
    "cloud":"Servicios en la nube",
    "generic":"Concepto visual",
}
VALID_KINDS=frozenset(CATEGORIES)
def tokens(text):
    clean=unicodedata.normalize("NFKD", text.casefold())
    clean="".join(c for c in clean if not unicodedata.combining(c))
    return set(re.findall(r"[a-z0-9]+",clean))
def classify(text):
    words=tokens(text)
    scores={kind:len(words.intersection(keywords)) for kind,keywords in CATEGORIES.items() if kind!="generic"}
    best=max(scores, key=scores.get)
    return best if scores[best]>0 else "generic"

def plan(storyboard, timing):
    scenes=storyboard.get("scenes")
    offsets=timing.get("offsets")
    if not isinstance(scenes,list) or not 1<=len(scenes)<=12:
        raise ValueError("Storyboard inválido: se requieren de 1 a 12 escenas.")
    if not isinstance(offsets,list) or len(offsets)!=len(scenes)+1:
        raise ValueError("Los tiempos de audio no coinciden con las escenas.")
    if abs(offsets[0])>0.001 or any(
        not isinstance(t,(float,int)) or isinstance(t,bool) or
        t<0 or t>900 for t in offsets
    ) or any(b-a<0.1 for a,b in zip(offsets,offsets[1:])):
        raise ValueError("Tiempos de audio inválidos.")
    result=[]
    for index,scene in enumerate(scenes):
        text=scene.get("voice",scene.get("text",""))
        if not isinstance(text,str) or not text.strip() or len(text)>300:
            raise ValueError("Texto de escena inválido.")
        # The allowed kind is derived from text, never from arbitrary user code.
        kind=classify(text)
        result.append({
            "index":index+1,
            "kind":kind,
            "label":LABELS[kind],
            "start":round(offsets[index],3),
            "duration":round(offsets[index+1]-offsets[index],3),
        })
    return {"version":1,"mode":"rules-v1","scenes":result,
            "total_duration":round(offsets[-1],3)}

def main():
    cli=argparse.ArgumentParser()
    cli.add_argument("--storyboard",required=True)
    cli.add_argument("--timing",required=True)
    cli.add_argument("--out",required=True)
    args=cli.parse_args()
    result=plan(
        json.loads(Path(args.storyboard).read_text(encoding="utf-8")),
        json.loads(Path(args.timing).read_text(encoding="utf-8")))
    dest=Path(args.out)
    dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("Director de escenas:",", ".join(s["kind"] for s in result["scenes"]))

if __name__=="__main__":
    main()
