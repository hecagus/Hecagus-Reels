#!/usr/bin/env python3
"""HEC REELS: independent 2.5D vertical reel renderer with local speech.

Requirements: Pillow, piper-tts, downloaded es_MX voice, ffmpeg. Storyboard JSON.
"""
import argparse
import json
import math
import shutil
import subprocess
import tempfile
import wave
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

BASE_W, BASE_H = 540, 960
VISUALS = {"question", "domain", "resolve", "connect", "summary", "abstract", "studio_home", "studio_script", "studio_key", "studio_render", "studio_results", "studio_free"}
BASE_BG = (7, 13, 28)
WHITE = (246, 250, 255)
MUTED = (167, 184, 207)
FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_BOLD_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def color(hexstr):
    s = hexstr.strip().lstrip('#')
    if len(s) != 6 or any(ch not in '0123456789abcdefABCDEF' for ch in s):
        raise ValueError('accent debe ser color hexadecimal #RRGGBB')
    return tuple(int(s[i:i+2], 16) for i in (0, 2, 4))


def font(sz, bold=False):
    path = FONT_BOLD_PATH if bold else FONT_PATH
    return ImageFont.truetype(path, sz)


def fit_lines(draw, text, use_font, max_w, max_lines=None):
    words = str(text).split()
    lines, line = [], ''
    for word in words:
        candidate = f'{line} {word}'.strip()
        if draw.textbbox((0, 0), candidate, font=use_font)[2] <= max_w:
            line = candidate
        else:
            if line:
                lines.append(line)
            line = word
    if line:
        lines.append(line)
    if max_lines and len(lines) > max_lines:
        raise ValueError(f'Texto demasiado largo para la composición: {text}')
    return lines


def rounded(draw, xy, radius, fill, outline=None, width=1):
    draw.rounded_rectangle(tuple(int(x) for x in xy), radius=int(radius), fill=fill, outline=outline, width=width)


def label(draw, text, cx, y, size, fill, bold=False):
    f = font(size, bold)
    bounds = draw.textbbox((0, 0), text, font=f)
    draw.text((int(cx-(bounds[2]-bounds[0])/2), int(y)), text, font=f, fill=fill)


def text_block(draw, text, y, size, fill, max_width=470, line_height=1.33, max_lines=None):
    f = font(size, True)
    lines = fit_lines(draw, text, f, max_width, max_lines=max_lines)
    for i, row in enumerate(lines):
        label(draw, row, BASE_W//2, y + int(i*size*line_height), size, fill, bold=True)
    return lines


def glow_circle(draw, x, y, r, rgb, p):
    for k in range(4, 0, -1):
        rr = r + 10*k
        alpha = max(6, int(30/k + 3*math.sin(p)))
        blended = tuple(int(BASE_BG[c]*(1-alpha/255)+rgb[c]*alpha/255) for c in range(3))
        draw.ellipse((x-rr, y-rr, x+rr, y+rr), outline=blended, width=3)
    draw.ellipse((x-r, y-r, x+r, y+r), fill=rgb)


def draw_browser(draw, x, y, w, h, accent, url='ejemplo.com'):
    rounded(draw, (x+7, y+12, x+w+7, y+h+12), 16, (8, 32, 55))
    rounded(draw, (x, y, x+w, y+h), 16, (24, 38, 62), outline=(76, 111, 139), width=2)
    draw.rounded_rectangle((x+15, y+12, x+w-15, y+40), radius=7, fill=(10, 20, 38))
    draw.ellipse((x+23, y+21, x+30, y+28), fill=(255, 110, 108))
    label(draw, url, x+w//2+5, y+19, 13, WHITE, bold=True)
    draw.rounded_rectangle((x+30, y+60, x+w-30, y+87), radius=5, fill=(47, 68, 88))
    draw.rounded_rectangle((x+30, y+98, x+w-100, y+114), radius=4, fill=accent)
    draw.rounded_rectangle((x+30, y+126, x+w-70, y+136), radius=4, fill=(94, 117, 141))


def line_packet(draw, a, b, t, accent):
    draw.line((a[0],a[1],b[0],b[1]), fill=(55, 96, 133), width=5)
    u = (math.sin(t*2.4-math.pi/2)+1)/2
    x = a[0]+u*(b[0]-a[0]); y=a[1]+u*(b[1]-a[1])
    glow_circle(draw, x, y, 6, accent, t)



def draw_studio_visual(draw, mode, t, accent):
    """Maquetas animadas simplificadas de la interfaz web real, sin capturas falsas."""
    rounded(draw,(52,355,488,735),22,(17,30,48),outline=(59,100,130),width=2)
    rounded(draw,(53,356,487,394),18,(23,48,69))
    draw.ellipse((67,370,75,378), fill=(255,114,120))
    draw.ellipse((83,370,91,378), fill=(255,206,109))
    draw.ellipse((99,370,107,378), fill=(92,220,150))
    label(draw,'HecAgus REELS',270,369,17,accent,True)
    if mode=='studio_home':
        label(draw,'Abre tu navegador',270,423,23,WHITE,True)
        rounded(draw,(81,472,459,532),13,(8,21,35),outline=accent,width=2)
        label(draw,'hecagus-reels.vercel.app',270,488,20,WHITE,True)
        label(draw,'ESTUDIO EN LA NUBE',270,564,16,MUTED,True)
        rounded(draw,(142,608,398,668),13,accent)
        label(draw,'ABRIR SITIO',270,626,19,BASE_BG,True)
    elif mode=='studio_script':
        label(draw,'Nuevo proyecto',270,421,23,WHITE,True)
        rounded(draw,(72,462,469,514),12,(18,45,64))
        rounded(draw,(257,466,465,510),9,(44,104,123))
        label(draw,'Tengo una idea',162,479,14,MUTED,True)
        label(draw,'Tengo el guion',361,478,14,WHITE,True)
        label(draw,'Narración por escenas',270,541,16,WHITE,True)
        rounded(draw,(76,577,464,674),13,(7,17,32),outline=(50,82,110),width=2)
        label(draw,'Escena uno...',270,590,19,WHITE,True)
        label(draw,'||',270,618,22,accent,True)
        label(draw,'Escena dos...',270,646,19,WHITE,True)
    elif mode=='studio_key':
        label(draw,'Configura la narración',270,423,20,WHITE,True)
        label(draw,'Voz: español mexicano',270,466,18,accent,True)
        rounded(draw,(87,508,453,565),12,(9,23,39),outline=(52,92,118),width=2)
        label(draw,'Velocidad     1.00×',270,524,19,WHITE,True)
        label(draw,'Clave privada del estudio',270,583,17,MUTED,True)
        rounded(draw,(87,622,453,680),12,(9,23,39),outline=accent,width=2)
        label(draw,'••••••••••••••••',270,638,21,WHITE,True)
    elif mode=='studio_render':
        label(draw,'Tu proyecto está listo',270,429,23,WHITE,True)
        rounded(draw,(87,485,453,560),15,accent)
        label(draw,'GENERAR MI REEL',270,512,21,BASE_BG,True)
        draw.line((270,577,270,629),fill=accent,width=5)
        draw.polygon([(257,621),(283,621),(270,639)],fill=accent)
        label(draw,'GITHUB ACTIONS',270,657,20,WHITE,True)
        label(draw,'Piper + FFmpeg',270,691,16,accent)
    elif mode=='studio_results':
        label(draw,'Tus renders',270,419,24,WHITE,True)
        rounded(draw,(80,474,460,535),12,(11,29,47),outline=(55,98,129))
        label(draw,'En cola   →   Generando',270,492,19,MUTED,True)
        rounded(draw,(80,552,460,614),12,(10,49,47),outline=(43,127,109))
        label(draw,'✓  LISTO',270,572,23,(120,239,191),True)
        rounded(draw,(129,639,410,697),11,accent)
        label(draw,'DESCARGAR ZIP',270,657,19,BASE_BG,True)
    elif mode=='studio_free':
        label(draw,'Dos maneras de crear',270,431,21,WHITE,True)
        rounded(draw,(84,491,456,558),12,(15,56,63),outline=accent,width=2)
        label(draw,'Tengo el guion',270,508,21,WHITE,True)
        label(draw,'Sin API adicional',270,535,13,(130,240,188))
        rounded(draw,(84,579,456,653),12,(25,32,52),outline=(62,77,101),width=2)
        label(draw,'Tengo una idea',270,595,20,WHITE,True)
        label(draw,'Requiere API de IA',270,626,14,(254,207,147))

def draw_visual(draw, scene, t, accent):
    v = scene['visual']
    if v.startswith('studio_'):
        draw_studio_visual(draw, v, t, accent)
        return
    phase = 0.5 + 0.5*math.sin(t*1.8)
    bob = math.sin(t*2.1) * 10
    if v == 'question':
        draw_browser(draw, 130, 340+int(bob), 280, 175, accent, '¿Dónde está la web?')
        glow_circle(draw, 270, 575, 17, accent, t)
        draw.arc((200, 565, 340, 650), 192, 348, fill=(72, 115, 150), width=4)
        label(draw, 'www', 270, 586, 27, WHITE, bold=True)
    elif v == 'domain':
        rounded(draw, (61, 364, 479, 462), 21, (22, 38, 60), outline=accent, width=2)
        label(draw, 'ejemplo.com', 270, 394, 37, WHITE, bold=True)
        draw.line((270, 479, 270, 553), fill=accent, width=5)
        draw.polygon([(257, 548), (283, 548), (270, 570)], fill=accent)
        rounded(draw, (143, 590, 396, 663), 17, (17, 51, 77))
        label(draw, '203.0.113.10', 270, 607, 26, accent, bold=True)
        label(draw, 'IP ficticia · demostración', 270, 677, 15, MUTED)
    elif v == 'resolve':
        # Local device / DNS service / returned IP
        rounded(draw, (48, 437, 170, 565), 17, (20, 42, 67), outline=(92, 132, 165), width=2)
        draw.rounded_rectangle((75, 457, 144, 527), radius=8, outline=WHITE, width=4)
        label(draw, 'MÓVIL', 110, 537, 13, WHITE, True)
        rounded(draw, (361, 437, 492, 565), 17, (20, 42, 67), outline=accent, width=2)
        for ix in range(2):
            draw.rounded_rectangle((392, 458+32*ix, 460, 477+32*ix), radius=5, fill=(49, 86, 118))
            draw.ellipse((449, 464+32*ix, 455, 470+32*ix), fill=accent)
        label(draw, 'DNS', 426, 539, 15, WHITE, True)
        line_packet(draw, (169, 491), (363, 491), t, accent)
        label(draw, '¿IP?', 266, 452, 21, WHITE, True)
        label(draw, 'RESPUESTA', 268, 592, 16, MUTED, True)
        label(draw, '203.0.113.10', 268, 619, 26, accent, True)
    elif v == 'connect':
        draw_browser(draw, 48, 401+int(bob), 202, 154, accent, 'navegador')
        rounded(draw, (332, 412-int(bob), 489, 565-int(bob)), 17, (20, 42, 67), outline=accent, width=2)
        for ix in range(3):
            rounded(draw, (351, 427+ix*31-int(bob), 468, 450+ix*31-int(bob)), 5, (47, 87, 118))
            draw.ellipse((451, 434+ix*31-int(bob), 457, 440+ix*31-int(bob)), fill=accent)
        label(draw, 'SERVIDOR', 410, 579, 14, WHITE, True)
        line_packet(draw, (255, 485), (330, 485), t, accent)
        label(draw, 'CONEXIÓN', 285, 630, 22, accent, True)
    elif v == 'abstract':
        # Animación genérica para cualquier tema, sin afirmar contenido que no esté en el texto.
        for i in range(3):
            x = 150 + 120*i
            y = 475 + int(18*math.sin(t*1.4 + i*1.8))
            r = 31 + i*5
            glow_circle(draw, x, y, r, accent if i == 1 else (38, 122, 172), t+i)
            if i < 2:
                draw.line((x+r, y+15, x+120-r, y+15), fill=(96, 171, 202), width=5)
        rounded(draw, (85, 608, 455, 672), 14, (22, 44, 70), outline=accent, width=2)
        label(draw, 'IDEA  ·  VOZ  ·  VIDEO', 270, 625, 19, WHITE, True)
    else:
        draw_browser(draw, 138, 325+int(bob), 264, 182, accent, 'tu navegador')
        glow_circle(draw, 270, 568, 36, accent, t)
        label(draw, 'DNS', 270, 556, 24, BASE_BG, True)
        rounded(draw, (90, 652, 450, 711), 13, (20, 51, 74), outline=accent, width=2)
        label(draw, 'LOCALIZAR ≠ DESCARGAR', 270, 669, 16, WHITE, True)


def render_frame(scene, scene_idx, total_scenes, local_time, duration, width, height, accent):
    scale = width / BASE_W
    if height != round(BASE_H*scale):
        raise ValueError('La resolución debe mantener proporción 9:16 exacta.')
    # Draw on the base canvas; upscale only when explicitly requested.
    canvas = Image.new('RGB', (BASE_W, BASE_H), BASE_BG)
    d = ImageDraw.Draw(canvas)
    t = local_time
    # Motion graphic background stripes + floating particles.
    for i in range(10):
        x = 18 + i*57 + 16*math.sin(t*0.3 + i)
        y = 165 + (i*79)%650 + 11*math.cos(t*0.6+i)
        r = 2 + i%3
        d.ellipse((x-r,y-r,x+r,y+r), fill=(29, 69, 97))
    d.ellipse((-120, -210, 650, 530), outline=(12, 45, 70), width=3)
    d.ellipse((-70, -140, 605, 540), outline=(11, 31, 53), width=3)
    rounded(d, (23, 25, 194, 63), 10, (28, 55, 70))
    d.text((38, 35), 'HEC REELS', font=font(17, True), fill=accent)
    d.text((404, 36), 'DEMO 2.5D', font=font(13), fill=MUTED)
    for i in range(total_scenes):
        left = 23+i*(494/total_scenes)
        rounded(d, (left, 82, left+max(4, 482/total_scenes), 88), 3, accent if i<=scene_idx else (52, 75, 99))
    # Intro text
    label(d, scene['heading'][:44], 270, 144, 18, accent, bold=True)
    title_size = 36
    while title_size > 20 and len(fit_lines(d, scene['text'], font(title_size, True), 460)) > 4:
        title_size -= 1
    # Ajuste de tipografía según longitud de texto.
    text_block(d, scene['text'], 211, title_size, WHITE, max_width=460, max_lines=4)
    draw_visual(d, scene, t, accent)
    # Subtitle line for the whole scene. This is explicitly NOT word-aligned.
    rounded(d, (23, 783, 517, 890), 15, (16, 30, 47), outline=(36, 68, 90), width=2)
    subtitle_size = 24
    while subtitle_size > 16 and len(fit_lines(d, scene['text'], font(subtitle_size, True), 446)) > 3:
        subtitle_size -= 1
    ff = font(subtitle_size, True)
    subs = fit_lines(d, scene['text'], ff, 446, max_lines=3)
    for idx, line in enumerate(subs):
        label(d, line, 270, 802+idx*31, subtitle_size, WHITE, True)
    rounded(d, (25, 904, 515, 912), 4, (42, 66, 87))
    fraction = min(1.0,max(0.0,local_time/max(0.01,duration)))
    if fraction > 0:
        rounded(d, (25, 904, 25+490*fraction, 912), 4, accent)
    d.text((24, 926), 'HECHO CON HERRAMIENTAS ABIERTAS', font=font(10), fill=MUTED)
    d.text((464, 926), f'{scene_idx+1:02d}/{total_scenes:02d}', font=font(12, True), fill=accent)
    return canvas if width == BASE_W else canvas.resize((width,height), Image.Resampling.BICUBIC)


def load_piper_voice(model_path):
    """Carga el modelo ONNX una sola vez (CPU, sin servicios externos)."""
    model_path = Path(model_path).expanduser().resolve()
    if not model_path.is_file() or not Path(str(model_path) + '.json').is_file():
        raise RuntimeError(
            'No se encontraron el modelo Piper y su configuración JSON en: '
            f'{model_path}\n'
            'Instala dependencias: python -m pip install -r requirements.txt\n'
            'Descarga el modelo: python -m piper.download_voices es_MX-claude-high --data-dir voices'
        )
    try:
        from piper import PiperVoice
    except ImportError as exc:
        raise RuntimeError(
            'No está instalado Piper. Ejecuta: python -m pip install -r requirements.txt'
        ) from exc
    return PiperVoice.load(str(model_path))


def synthesize_wav(voice, text, dest, speech_rate=1.0):
    """Piper 1.8: sintetiza PCM WAV con un ajuste de velocidad."""
    from piper import SynthesisConfig
    with wave.open(str(dest), 'wb') as wav_file:
        voice.synthesize_wav(
            text, wav_file,
            syn_config=SynthesisConfig(length_scale=1.0 / speech_rate)
        )


def join_voice_wavs(voice_wavs, target, gap_before=0.20, gap_after=0.62):
    """Empalma WAV PCM y calcula marcas de tiempo reales para cada escena.

    No presupone frecuencia de muestreo ni duración de TTS. La SRT sigue
    alineada por escena, no por palabra.
    """
    params = None
    audio, segments = bytearray(), []
    for path in voice_wavs:
        with wave.open(str(path), 'rb') as wav_file:
            p = wav_file.getparams()
            if p.comptype != 'NONE' or p.sampwidth != 2 or p.nchannels < 1:
                raise RuntimeError(f'Piper devolvió un WAV PCM incompatible: {path}')
            if p.nframes <= 0:
                raise RuntimeError(f'Piper devolvió un WAV sin audio: {path}')
            if params is None:
                params = p
            elif (p.sampwidth, p.framerate, p.nchannels) != (params.sampwidth, params.framerate, params.nchannels):
                raise RuntimeError('Piper devolvió WAV con formatos distintos entre escenas')
            data = wav_file.readframes(p.nframes)
            bytes_per_second = p.framerate * p.nchannels * p.sampwidth
            start = len(audio) / bytes_per_second
            before_frames = round(gap_before * p.framerate)
            after_frames = round(gap_after * p.framerate)
            audio.extend(bytes(before_frames * p.nchannels * p.sampwidth))
            speech_start = len(audio) / bytes_per_second
            audio.extend(data)
            speech_end = len(audio) / bytes_per_second
            audio.extend(bytes(after_frames * p.nchannels * p.sampwidth))
            end = len(audio) / bytes_per_second
            segments.append((start, speech_start, speech_end, end))
    if params is None:
        raise RuntimeError('No hay escenas para sintetizar')
    with wave.open(str(target), 'wb') as writer:
        writer.setnchannels(params.nchannels)
        writer.setsampwidth(params.sampwidth)
        writer.setframerate(params.framerate)
        writer.writeframes(audio)
    return target, segments


def make_voice(scenes, tmp, model_path, speech_rate=1.0):
    voice = load_piper_voice(model_path)
    files = []
    for idx, scene in enumerate(scenes):
        target = tmp / f'voice-{idx}.wav'
        synthesize_wav(voice, scene['voice'], target, speech_rate)
        files.append(target)
    return join_voice_wavs(files, tmp / 'narration.wav')


def srtstamp(sec):
    milli = int(round(sec*1000)); h, remain = divmod(milli, 3600000)
    m, remain = divmod(remain, 60000); s, ms=divmod(remain, 1000)
    return f'{h:02d}:{m:02d}:{s:02d},{ms:03d}'


def validate(raw):
    if not isinstance(raw, dict) or not isinstance(raw.get('scenes'), list):
        raise ValueError('JSON debe contener scenes: []')
    scenes = raw['scenes']
    if not 1 <= len(scenes) <= 12:
        raise ValueError('Se permiten de 1 a 12 escenas')
    for idx, sc in enumerate(scenes):
        if not isinstance(sc, dict) or not all(k in sc and isinstance(sc[k], str) and sc[k].strip() for k in ('heading','text','voice','visual')):
            raise ValueError(f'Escena {idx+1}: faltan heading/text/voice/visual válidos')
        if sc['visual'] not in VISUALS:
            raise ValueError(f'Escena {idx+1}: visual desconocido {sc["visual"]}')
        if len(sc['text']) > 140 or len(sc['heading']) > 44 or len(sc['voice']) > 300:
            raise ValueError(f'Escena {idx+1}: texto excesivamente largo para diseño')
    color(raw.get('accent', '#4FE0F7'))
    return scenes


def main():
    ap = argparse.ArgumentParser(description='Renderiza reels técnicos 2.5D verticales (independiente de DASDINGO)')
    ap.add_argument('--storyboard', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--resolution', default='540x960', help='Ancho x alto, proporción 9:16')
    ap.add_argument('--fps', type=int, default=24)
    ap.add_argument('--piper-model', default='voices/es_MX-claude-high.onnx',
                    help='Ruta al modelo Piper .onnx (requiere .onnx.json al lado)')
    ap.add_argument('--speech-rate', type=float, default=1.0,
                    help='Multiplicador de velocidad: 1.0 normal, 1.1 más rápido, 0.9 más lento')
    args = ap.parse_args()
    if not shutil.which('ffmpeg'):
        raise SystemExit('Instala ffmpeg antes de renderizar.')
    if not math.isfinite(args.speech_rate) or not 0.75 <= args.speech_rate <= 1.35:
        raise SystemExit('speech-rate debe estar entre 0.75 y 1.35.')
    if not 8 <= args.fps <= 60:
        raise SystemExit('fps debe estar entre 8 y 60.')
    try:
        w,h = [int(s) for s in args.resolution.lower().split('x')]
    except Exception:
        raise SystemExit('--resolution debe ser anchoXalto, ej. 540x960')
    if w<270 or w>1080 or w*16!=h*9 or (w%2) or (h%2):
        raise SystemExit('Resolución inválida; usa 540x960, 720x1280 o 1080x1920.')
    raw = json.loads(Path(args.storyboard).read_text(encoding='utf8'))
    scenes = validate(raw)
    accent = color(raw.get('accent','#4FE0F7'))
    out = Path(args.out).resolve()
    out.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='hecreels_') as td:
        tmp = Path(td)
        try:
            voice_path, segments = make_voice(scenes, tmp, args.piper_model, args.speech_rate)
        except RuntimeError as exc:
            raise SystemExit(str(exc)) from exc
        offsets = [0]
        for start, speech_start, speech_end, end in segments:
            offsets.append(end)
        duration = offsets[-1]
        frame_count = math.ceil(duration*args.fps)
        # Render frames as raw RGB, then mux original voice without generating thousands of PNGs.
        silent = tmp/'silent.mp4'
        command = ['ffmpeg','-loglevel','error','-y','-f','rawvideo','-vcodec','rawvideo','-pix_fmt','rgb24','-s',f'{w}x{h}',
                   '-r',str(args.fps),'-i','-','-c:v','libx264','-preset','ultrafast','-crf','23','-pix_fmt','yuv420p',str(silent)]
        proc = subprocess.Popen(command,stdin=subprocess.PIPE,stderr=subprocess.PIPE)
        import bisect
        try:
            for frame_i in range(frame_count):
                t = frame_i/args.fps
                idx = min(len(scenes)-1, bisect.bisect_right(offsets, t)-1)
                frame = render_frame(scenes[idx],idx,len(scenes),t-offsets[idx],offsets[idx+1]-offsets[idx],w,h,accent)
                proc.stdin.write(frame.tobytes())
                if frame_i % max(1, args.fps*5) == 0:
                    print(f'Progreso: {frame_i}/{frame_count} fotogramas',flush=True)
        except Exception:
            proc.kill()
            raise
        finally:
            try: proc.stdin.close()
            except Exception: pass
        err = proc.stderr.read().decode(errors='replace')
        proc.stderr.close()
        if proc.wait() != 0:
            raise RuntimeError('FFmpeg falló al codificar: '+err[-1200:])
        subprocess.run(['ffmpeg','-loglevel','error','-y','-i',str(silent),'-i',str(voice_path),
                        '-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','aac','-b:a','128k',
                        '-t',f'{duration:.3f}','-movflags','+faststart',str(out)],check=True)
        cover = render_frame(scenes[0],0,len(scenes),.5,offsets[1],w,h,accent)
        cover.save(out.with_name(out.stem+'_portada.png'))
        srt_lines=[]
        for i, sc in enumerate(scenes):
            start, speech_start, speech_end, end = segments[i]
            srt_lines.extend([str(i+1),f'{srtstamp(speech_start)} --> {srtstamp(speech_end)}',sc['text'],''])
        out.with_suffix('.srt').write_text('\n'.join(srt_lines),encoding='utf8')
        out.with_name(out.stem+'_titulo.txt').write_text(raw.get('title','Reel explicativo')+'\n',encoding='utf8')
        out.with_name(out.stem+'_descripcion.txt').write_text(raw.get('description','')+'\n',encoding='utf8')
        print(f'Video creado: {out}\nDuración: {duration:.1f} s\nEscenas: {len(scenes)}')


if __name__ == '__main__':
    main()