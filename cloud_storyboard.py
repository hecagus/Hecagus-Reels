#!/usr/bin/env python3
"""Convierte texto ingresado en GitHub Actions en storyboard sin modelo generativo."""
import argparse
import json
import os
import re
from pathlib import Path

def normalize(text):
    return re.sub(r'\s+', ' ', text).strip()

def build_storyboard(text):
    clean = text.strip()
    if not clean:
        raise ValueError('Escribe un texto para narrar.')
    chunks = [normalize(piece) for piece in clean.split('||')]
    if any(not c for c in chunks):
        raise ValueError('Hay una escena vacía. No coloques || al principio o al final.')
    if not 1 <= len(chunks) <= 6:
        raise ValueError('Se permiten de 1 a 6 escenas, separadas por ||.')
    for index, chunk in enumerate(chunks, 1):
        if len(chunk) > 105:
            raise ValueError(f'Escena {index}: máximo 105 caracteres; divide con ||.')
        if any(len(token) > 30 for token in chunk.split()):
            raise ValueError(f'Escena {index}: divide palabras de más de 30 caracteres.')
        if len(chunk) < 2:
            raise ValueError(f'Escena {index}: mínimo 2 caracteres.')
    return {
        'title': chunks[0][:65],
        'description': 'Video narrado en español mexicano y creado con HEC REELS.',
        'accent': '#4FE0F7',
        'scenes': [
            {'heading': f'ESCENA {idx:02d}', 'text': chunk, 'voice': chunk, 'visual': 'abstract'}
            for idx, chunk in enumerate(chunks, 1)
        ],
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', default='output/storyboard_cloud.json')
    args = parser.parse_args()
    story = build_storyboard(os.environ.get('HEC_REEL_TEXT', ''))
    output = Path(args.out)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(story, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
    print(f'Storyboard generado: {output} ({len(story["scenes"])} escena/s)')

if __name__ == '__main__':
    main()
