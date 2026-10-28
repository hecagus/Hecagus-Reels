"""Pruebas del convertidor de entrada para GitHub Actions."""
import unittest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from cloud_storyboard import build_storyboard
from render import validate, render_frame, color

class CloudInputTests(unittest.TestCase):
    def test_two_scenes_are_valid(self):
        story = build_storyboard('Primera escena||Segunda escena')
        self.assertEqual(len(validate(story)), 2)
        self.assertEqual(story['scenes'][0]['visual'], 'abstract')
        self.assertEqual(story['scenes'][1]['voice'], 'Segunda escena')

    def test_generic_visual_renders(self):
        story = build_storyboard('Narración de prueba')
        frame = render_frame(story['scenes'][0], 0, 1, .4, 3, 540, 960, color('#4FE0F7'))
        self.assertEqual(frame.size, (540, 960))

    def test_rejects_long_text(self):
        with self.assertRaisesRegex(ValueError, 'máximo 105'):
            build_storyboard('a' * 106)

    def test_rejects_empty_chunk(self):
        with self.assertRaisesRegex(ValueError, 'escena vacía'):
            build_storyboard('hola ||')

    def test_long_sentence_fits(self):
        text = ('Este es un ejemplo de texto de narración que tiene muchas palabras y sirve para representar un video de explicación extendida en español.')[:105]
        story = build_storyboard(text)
        frame = render_frame(story['scenes'][0], 0, 1, .4, 3, 540, 960, color('#4FE0F7'))
        self.assertEqual(frame.size, (540, 960))

    def test_rejects_long_token(self):
        with self.assertRaisesRegex(ValueError, 'palabras'):
            build_storyboard('A' * 70)

    def test_rejects_many_scenes(self):
        with self.assertRaisesRegex(ValueError, '1 a 6'):
            build_storyboard('||'.join(['escena válida']*7))

if __name__ == '__main__':
    unittest.main()
