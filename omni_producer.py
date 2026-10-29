#!/usr/bin/env python3
"""HEC REELS: idea -> guion Gemini -> escenas Omni -> MP4. Sin reintentos pagados."""
import argparse
import base64
import json
import os
from pathlib import Path
import re
import subprocess
import time
from urllib import request, error

API = "https://generativelanguage.googleapis.com/v1beta"
VIDEO_MODEL = "gemini-omni-1.1-flash"
TEXT_MODEL = "gemini-2.5-flash"

def idea_valida(idea):
    if not isinstance(idea, str):
        raise ValueError("Idea no válida")
    idea = " ".join(idea.split())
    if not 8 <= len(idea) <= 350:
        raise ValueError("La idea debe tener entre 8 y 350 caracteres")
    return idea

def duracion_valida(s):
    n = int(s)
    if n not in (6, 60):
        raise ValueError("Duración no válida: solamente 6 o 60 segundos")
    return n

def google_json(path, body=None, timeout=360):
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        raise RuntimeError("Falta GEMINI_API_KEY en los secretos de GitHub")
    data = json.dumps(body, ensure_ascii=False).encode("utf-8") if body is not None else None
    req = request.Request(API + path, data=data, method="POST" if data else "GET",
        headers={"x-goog-api-key": key, "Content-Type": "application/json"})
    try:
        with request.urlopen(req, timeout=timeout) as response:
            return json.load(response)
    except error.HTTPError as exc:
        raise RuntimeError(f"API de Google: HTTP {exc.code} en {path}") from None

def validar_guion(payload, count):
    scenes = payload.get("scenes")
    if not isinstance(scenes, list) or len(scenes) != count:
        raise ValueError("El guion no contiene el número de escenas solicitado")
    fixed = []
    for scene in scenes:
        visual, dialogue = scene.get("visual"), scene.get("dialogue")
        if not isinstance(visual, str) or not 10 <= len(visual.strip()) <= 360:
            raise ValueError("Descripción visual inválida")
        if not isinstance(dialogue, str) or not 2 <= len(dialogue.strip()) <= 170:
            raise ValueError("Diálogo inválido")
        fixed.append({"visual": visual.strip(), "dialogue": dialogue.strip()})
    title = payload.get("title", "HEC REELS")
    return {"title": str(title)[:90], "scenes": fixed}

def escribir_guion(idea, count):
    prompt = (
        "Eres guionista de cortos cómicos y director de animación. Idea del usuario: " + idea +
        ". Escribe exactamente " + str(count) + " escenas consecutivas de 6 segundos, "
        "para un video 3D vertical 9:16 con principio, desarrollo y remate. "
        "Diálogos naturales en español mexicano, máximo 12 palabras pronunciadas por escena, "
        "con nombre del hablante. Mantén personajes y vestuario consistentes. "
        "No inventes afirmaciones verificables. Escenas visuales concretas. "
        'Devuelve únicamente JSON: {"title":"...","scenes":[{"visual":"...","dialogue":"..."}]}.'
    )
    response = google_json("/models/" + TEXT_MODEL + ":generateContent", {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseMimeType": "application/json", "maxOutputTokens": 3200}
    })
    try:
        parts = response["candidates"][0]["content"]["parts"]
        return validar_guion(json.loads("".join(p.get("text", "") for p in parts)), count)
    except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
        raise RuntimeError("Gemini no entregó un guion JSON válido") from exc

def buscar_video(obj):
    if isinstance(obj, dict):
        if obj.get("type") == "video" and (obj.get("uri") or obj.get("data")):
            return obj
        for value in obj.values():
            found = buscar_video(value)
            if found:
                return found
    if isinstance(obj, list):
        for value in obj:
            found = buscar_video(value)
            if found:
                return found
    return None

def obtener_video(video, destino):
    if video.get("data"):
        destino.write_bytes(base64.b64decode(video["data"], validate=True))
        return
    uri = video.get("uri", "")
    match = re.search(r"(?:^|/)files/([A-Za-z0-9_-]+)(?:$|[:/?])", uri)
    if not match:
        raise RuntimeError("La respuesta no contiene un identificador de video")
    ident = match.group(1)
    for _ in range(90):
        status = google_json("/files/" + ident, timeout=30).get("state", "")
        if status == "ACTIVE":
            break
        if status == "FAILED":
            raise RuntimeError("Google falló al procesar el video")
        time.sleep(5)
    else:
        raise RuntimeError("Tiempo agotado esperando el video")
    req = request.Request(API + "/files/" + ident + ":download?alt=media",
        headers={"x-goog-api-key": os.environ["GEMINI_API_KEY"]})
    try:
        with request.urlopen(req, timeout=180) as stream, destino.open("wb") as target:
            while True:
                block = stream.read(1024 * 1024)
                if not block:
                    break
                target.write(block)
    except error.HTTPError as exc:
        raise RuntimeError(f"No se pudo descargar el video: HTTP {exc.code}") from None

def crear_escena(idea, guion, scene, index, total, destino):
    prompt = (
        "Produce a six-second 3D animated cinematic video, vertical portrait 9:16, "
        "single continuous shot, no cuts, with native audio and synchronized mouth movements. "
        "ALL spoken dialogue in Mexican Spanish, exactly as written, no subtitles or added speech. "
        "Maintain the exact same characters and clothing throughout the story. "
        "When present, HecAgus is a Mexican adult man with short dark hair, a black t-shirt "
        "and a slightly rounded belly. ChatGPT is an expressive floating digital hologram. "
        "Story: " + idea + ". Title: " + guion["title"] + ". Scene " + str(index) +
        " of " + str(total) + ". Action: " + scene["visual"] +
        ". Spoken words and character: " + scene["dialogue"]
    )
    result = google_json("/interactions", {
        "model": VIDEO_MODEL,
        "input": prompt,
        "response_format": {"type": "video", "aspect_ratio": "9:16", "resolution": "720p", "delivery": "uri"},
        "background": False, "store": False, "stream": False
    })
    video = buscar_video(result.get("steps", [])) or buscar_video(result.get("output_video"))
    if not video:
        raise RuntimeError("Gemini Omni no devolvió un video")
    obtener_video(video, destino)
    if destino.stat().st_size < 2048:
        raise RuntimeError("Archivo de escena incompleto")

def ejecutar(command):
    subprocess.run(command, check=True, stdout=subprocess.DEVNULL)

def verificar_av(file, segundos=None):
    out = subprocess.check_output(["ffprobe", "-v", "error",
        "-show_entries", "stream=codec_type:format=duration", "-of", "json", str(file)], text=True)
    meta = json.loads(out)
    kinds = {s.get("codec_type") for s in meta.get("streams", [])}
    if not {"audio", "video"}.issubset(kinds):
        raise RuntimeError("La salida debe contener audio y video")
    actual = float(meta.get("format", {}).get("duration", 0))
    if segundos is not None and abs(actual - segundos) > 0.25:
        raise RuntimeError(f"Duración inesperada: {actual:.2f} s (esperados {segundos})")

def normalizar(entrada, salida):
    verificar_av(entrada)
    ejecutar(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(entrada),
        "-map", "0:v:0", "-map", "0:a:0",
        "-vf", "scale=720:1280:force_original_aspect_ratio=decrease,"
               "pad=720:1280:(ow-iw)/2:(oh-ih)/2,setsar=1,"
               "fps=24,tpad=stop_mode=clone:stop_duration=6",
        "-af", "apad", "-t", "6", "-c:v", "libx264", "-preset", "veryfast",
        "-crf", "23", "-pix_fmt", "yuv420p", "-c:a", "aac",
        "-ar", "48000", "-ac", "2", "-movflags", "+faststart", str(salida)])
    verificar_av(salida, 6)

def montar(partes, destino, segundos):
    listado = destino.parent / "lista_concat.txt"
    listado.write_text("".join("file '" + str(p.resolve()) + "'\n" for p in partes), encoding="utf-8")
    ejecutar(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-f", "concat", "-safe", "0", "-i", str(listado), "-t", str(segundos),
        "-c", "copy", "-movflags", "+faststart", str(destino)])
    verificar_av(destino, segundos)
    ejecutar(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-i", str(destino), "-frames:v", "1", str(destino.parent / "hec_omni_portada.png")])

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="output")
    output = Path(parser.parse_args().output)
    idea = idea_valida(os.getenv("HEC_OMNI_IDEA", ""))
    segundos = duracion_valida(os.getenv("HEC_OMNI_DURATION", "6"))
    if os.getenv("HEC_OMNI_COST_ACCEPTED") != "SI":
        raise RuntimeError("Falta consentimiento para consumir API de pago")
    if not os.getenv("GEMINI_API_KEY"):
        raise RuntimeError("Falta GEMINI_API_KEY en GitHub")
    output.mkdir(parents=True, exist_ok=True)
    count = segundos // 6
    guion = escribir_guion(idea, count)
    (output / "hec_omni_guion.json").write_text(
        json.dumps({"idea": idea, **guion}, ensure_ascii=False, indent=2), encoding="utf-8")
    clips = []
    for index, scene in enumerate(guion["scenes"], 1):
        print(f"Generando escena {index}/{count}... (una sola petición facturable)")
        bruto = output / f"original_{index:02d}.mp4"
        clip = output / f"escena_{index:02d}.mp4"
        crear_escena(idea, guion, scene, index, count, bruto)
        normalizar(bruto, clip)
        bruto.unlink()
        clips.append(clip)
    montar(clips, output / "hec_omni.mp4", segundos)
    print(f"MP4 con audio y video verificado: {segundos} segundos")

if __name__ == "__main__":
    main()
