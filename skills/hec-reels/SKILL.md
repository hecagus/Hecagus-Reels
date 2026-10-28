---
name: hec-reels
description: Crear reels verticales con Piper en español mexicano, animación procedural 2.5D, portada y subtítulos por escena. Usar para video explicativo corto.
---

# Skill HEC REELS

Sigue primero AGENTS.md en la raíz.

## Flujo
- Crear o adaptar examples/<nombre>.json, con textos en español mexicano y visuales coherentes.
- Verificar Piper y el modelo en voices/, según README.md, o usar GitHub Actions sin instalar nada localmente.
- Probar solo voz si hace falta: python preview_voice.py --out output/prueba_piper.wav.
- Renderizar: python render.py --storyboard examples/<nombre>.json --out output/<nombre>.mp4.
- Inspeccionar MP4, portada, audio y SRT. Informar limitaciones.

## Visuales permitidos
question, domain, resolve, connect, summary, abstract.

## Límites
No hay subtítulos palabra por palabra ni 3D real. Piper no garantiza pronunciación perfecta. No reemplazar Piper por eSpeak sin indicarlo. No atribuir código privativo de terceros a esta skill.
