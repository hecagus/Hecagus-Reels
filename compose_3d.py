#!/usr/bin/env python3
"""Compone los clips Blender por escena con duraciones reales de Piper.

FFmpeg repite solo el clip de SU escena, no el mismo clip para todo el reel.
Se usa el MP4 2.5D inicial únicamente como fuente de narración AAC.
"""
import argparse
import json
import math
import subprocess
import tempfile
from pathlib import Path

def run(command):
    subprocess.run(command,check=True)

def valid_plan(data):
    shots=data.get("scenes")
    if not isinstance(shots,list) or not 1<=len(shots)<=12:
        raise ValueError("Plan de escenas vacío o demasiado largo.")
    for idx,shot in enumerate(shots,1):
        if shot.get("index")!=idx:
            raise ValueError("Índice de escena incorrecto.")
        d=shot.get("duration")
        if not isinstance(d,(float,int)) or not math.isfinite(d) or not .1<=d<=180:
            raise ValueError("Duración inválida.")
    return shots

def compose(plan,frames,audio_source,output,ffmpeg="ffmpeg"):
    shots=valid_plan(plan)
    frames=Path(frames)
    output=Path(output)
    output.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="hec_3d_mix_") as tmp:
        tmp=Path(tmp)
        manifest=[]
        for shot in shots:
            number=shot["index"]
            directory=frames/("scene_%02d"%number)
            if not (directory/"0001.png").is_file():
                raise FileNotFoundError("Sin fotogramas de escena %d"%number)
            clip=tmp/("scene_%02d.mp4"%number)
            run([ffmpeg,"-hide_banner","-loglevel","error","-y",
                "-stream_loop","-1","-framerate","12",
                "-i",str(directory/"%04d.png"),
                "-t",f'{shot["duration"]:.3f}',
                "-r","24","-c:v","libx264","-preset","veryfast",
                "-crf","25","-pix_fmt","yuv420p",str(clip)])
            manifest.append("file '"+clip.as_posix()+"'")
        playlist=tmp/"manifest.txt"
        playlist.write_text("\n".join(manifest)+"\n",encoding="utf8")
        silent=tmp/"silent.mp4"
        run([ffmpeg,"-hide_banner","-loglevel","error","-y",
            "-f","concat","-safe","0","-i",str(playlist),
            "-c","copy",str(silent)])
        # Keep the original Piper audio, never replace it with a synthetic dummy.
        run([ffmpeg,"-hide_banner","-loglevel","error","-y",
            "-i",str(silent),"-i",str(audio_source),
            "-map","0:v:0","-map","1:a:0","-c:v","copy",
            "-c:a","copy","-shortest","-movflags","+faststart",str(output)])

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--plan",required=True)
    parser.add_argument("--frames",required=True)
    parser.add_argument("--narrated-video",required=True)
    parser.add_argument("--out",required=True)
    args=parser.parse_args()
    data=json.loads(Path(args.plan).read_text(encoding="utf8"))
    compose(data,args.frames,args.narrated_video,args.out)
    print("MP4 3D creado:",args.out)

if __name__=="__main__":
    main()
