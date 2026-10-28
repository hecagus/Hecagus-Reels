"""Pruebas de canalización: modelo Piper simulado, sin descargas ni voces reales."""
import contextlib
import io
import json
import math
import struct
import subprocess
import sys
import tempfile
import types
import unittest
import wave
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import render

class MockConfig:
    def __init__(self, length_scale=1.0):
        self.length_scale = length_scale

class MockPiperVoice:
    loads = 0
    utterances = []

    @classmethod
    def load(cls, path):
        cls.loads += 1
        return cls()

    def synthesize_wav(self, text, wav_file, syn_config):
        self.utterances.append((text, syn_config.length_scale))
        sample_rate = 22050
        frame_count = round(sample_rate * 0.45 * syn_config.length_scale)
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        pcm = b''.join(struct.pack('<h', int(2400 * math.sin(2 * math.pi * 330 * i / sample_rate)))
                       for i in range(frame_count))
        wav_file.writeframes(pcm)

@contextlib.contextmanager
def fake_voice_environment(tmp):
    model_path = tmp / 'fake.onnx'
    model_path.write_bytes(b'MOCK, NOT REAL ONNX')
    Path(f'{model_path}.json').write_text('{}')
    fake_piper = types.ModuleType('piper')
    fake_piper.PiperVoice = MockPiperVoice
    fake_piper.SynthesisConfig = MockConfig
    MockPiperVoice.loads = 0
    MockPiperVoice.utterances = []
    with patch.dict(sys.modules, {'piper': fake_piper}):
        yield model_path

class VoiceTests(unittest.TestCase):
    def test_missing_model_is_actionable(self):
        with self.assertRaisesRegex(RuntimeError, 'download_voices'):
            render.load_piper_voice('not-a-model.onnx')

    def test_synthesis_and_scene_timing(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            with fake_voice_environment(tmp) as model:
                audio, segments = render.make_voice(
                    [{'voice': 'Primera frase'}, {'voice': 'Segunda frase'}], tmp, model, 1.1
                )
            self.assertEqual(MockPiperVoice.loads, 1, 'Piper se debe cargar una sola vez')
            self.assertEqual(len(MockPiperVoice.utterances), 2)
            self.assertAlmostEqual(MockPiperVoice.utterances[0][1], 1 / 1.1)
            self.assertEqual(len(segments), 2)
            self.assertAlmostEqual(segments[0][0], 0)
            self.assertAlmostEqual(segments[0][1], 0.20)
            self.assertAlmostEqual(segments[0][-1], segments[1][0])
            with wave.open(str(audio)) as wav_file:
                self.assertEqual(wav_file.getframerate(), 22050)
                self.assertEqual(wav_file.getnchannels(), 1)
                self.assertAlmostEqual(wav_file.getnframes() / 22050, segments[-1][-1], places=3)

    @unittest.skipUnless(__import__('shutil').which('ffmpeg'), 'FFmpeg no disponible')
    def test_end_to_end_uses_piper_interface(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            storyboard = tmp / 'simple.json'
            storyboard.write_text(json.dumps({'title': 'Prueba', 'scenes': [
                {'heading': 'PRUEBA', 'text': 'Así funciona la red.',
                 'voice': 'Así funciona la red.', 'visual': 'question'}
            ]}, ensure_ascii=False), encoding='utf8')
            out = tmp / 'clip.mp4'
            with fake_voice_environment(tmp) as model:
                arguments = ['render.py', '--storyboard', str(storyboard), '--out', str(out),
                             '--piper-model', str(model), '--resolution', '270x480', '--fps', '8']
                with patch.object(sys, 'argv', arguments), contextlib.redirect_stdout(io.StringIO()):
                    render.main()
            self.assertGreater(out.stat().st_size, 1000)
            if __import__('shutil').which('ffprobe'):
                tracks = subprocess.check_output([
                    'ffprobe', '-v', 'error', '-show_entries', 'stream=codec_name',
                    '-of', 'csv=p=0', str(out)], text=True).splitlines()
                self.assertIn('h264', tracks)
                self.assertIn('aac', tracks)
            self.assertTrue((tmp / 'clip.srt').is_file())
            self.assertTrue((tmp / 'clip_portada.png').is_file())
            content = (tmp / 'clip.srt').read_text(encoding='utf8')
            self.assertIn('00:00:00,200 -->', content)

if __name__ == '__main__':
    unittest.main()
