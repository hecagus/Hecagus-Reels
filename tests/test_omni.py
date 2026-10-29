import unittest
from unittest.mock import patch
import omni_producer as o

class TestOmni(unittest.TestCase):
    def test_idea_validation(self):
        self.assertEqual(o.idea_valida("  ChatGPT  regaña  a HecAgus  "), "ChatGPT regaña a HecAgus")
        for invalid in ("hola", "", "a" * 351):
            with self.assertRaises(ValueError):
                o.idea_valida(invalid)

    def test_duration(self):
        self.assertEqual(o.duracion_valida("60"), 60)
        with self.assertRaises(ValueError):
            o.duracion_valida("8")

    def test_story_validation(self):
        data = {"title": "Sí, Chat", "scenes": [{
            "visual": "ChatGPT habla en una oficina con HecAgus.",
            "dialogue": "HecAgus: Sí, Chat."
        }]}
        self.assertEqual(o.validar_guion(data, 1)["title"], "Sí, Chat")
        with self.assertRaises(ValueError):
            o.validar_guion(data, 10)

    def test_rest_extract_video(self):
        obj = {"steps": [{"type": "model_output", "content": [
            {"type": "video", "uri": "files/video123", "mime_type": "video/mp4"}]}]}
        self.assertEqual(o.buscar_video(obj)["uri"], "files/video123")
        self.assertIsNone(o.buscar_video({"steps": []}))

    def test_no_paid_calls_without_consent(self):
        with patch.dict("os.environ", {
            "HEC_OMNI_IDEA": "ChatGPT regaña a HecAgus por iniciar proyectos nuevos",
            "HEC_OMNI_DURATION": "6", "HEC_OMNI_COST_ACCEPTED": "NO",
            "GEMINI_API_KEY": "testing-only"
        }):
            with patch("sys.argv", ["omni_producer.py"]):
                with patch.object(o, "escribir_guion") as paid_call:
                    with self.assertRaisesRegex(RuntimeError, "consentimiento"):
                        o.main()
                    paid_call.assert_not_called()

if __name__ == "__main__":
    unittest.main()
