#!/usr/bin/env python3
"""Genera una muestra WAV con la voz local Piper configurada en HEC REELS."""
import argparse
from pathlib import Path
from render import load_piper_voice, synthesize_wav

def main():
    ap = argparse.ArgumentParser(description='Previsualiza la voz española mexicana de Piper')
    ap.add_argument('--text', default='Hola, soy la voz de HEC REELS. Esto es una prueba en español mexicano.')
    ap.add_argument('--out', default='output/prueba_piper.wav')
    ap.add_argument('--piper-model', default='voices/es_MX-claude-high.onnx')
    ap.add_argument('--speech-rate', type=float, default=1.0)
    args = ap.parse_args()
    if not 0.75 <= args.speech_rate <= 1.35:
        ap.error('--speech-rate debe estar entre 0.75 y 1.35')
    output = Path(args.out)
    output.parent.mkdir(parents=True, exist_ok=True)
    try:
        synthesize_wav(load_piper_voice(args.piper_model), args.text, output, args.speech_rate)
    except RuntimeError as exc:
        ap.exit(1, f'{exc}\n')
    print(f'Muestra creada: {output.resolve()}')

if __name__ == '__main__':
    main()
