import unittest
from scene_director import classify,plan
from compose_3d import valid_plan

class DirectorTests(unittest.TestCase):
    def test_topic_objects(self):
        samples={
            "payment":"La terminal acepta pagos con tarjeta.",
            "network":"El router conecta redes wifi.",
            "food":"Prepara pasta en la cocina.",
            "motorcycle":"La moto tiene dos llantas y un motor.",
            "cloud":"Firebase es un servicio cloud en la nube.",
            "generic":"Una historia sobre la paciencia."
        }
        for expected,text in samples.items():
            with self.subTest(expected=expected):
                self.assertEqual(classify(text),expected)
    def test_case_and_accents(self):
        self.assertEqual(classify("Conexión por WÍFI"),"network")
        self.assertEqual(classify("Pago con TARJETA"),"payment")
    def test_multiple_scenes_keep_audio_boundaries(self):
        story={"scenes":[{"voice":"Pagar con tarjeta."},{"voice":"Ahora la conexión wifi."}]}
        timing={"offsets":[0,1.25,3.87]}
        result=plan(story,timing)
        self.assertEqual([s["kind"] for s in result["scenes"]],["payment","network"])
        self.assertEqual([s["duration"] for s in result["scenes"]],[1.25,2.62])
        self.assertEqual(result["total_duration"],3.87)
        self.assertEqual(len(valid_plan(result)),2)
    def test_reject_mismatched_audio(self):
        with self.assertRaisesRegex(ValueError,"coinciden"):
            plan({"scenes":[{"voice":"Pago"}]},{"offsets":[0]})
    def test_reject_bad_timing(self):
        with self.assertRaises(ValueError):
            plan({"scenes":[{"voice":"Pago"}]},{"offsets":[0,0]})
    def test_avoid_unbounded_shots(self):
        with self.assertRaises(ValueError):
            valid_plan({"scenes":[{"index":1,"duration":9999}]})
    def test_never_execute_user_text(self):
        story={"scenes":[{"voice":"__import__('os').system('echo exploit')"}]}
        self.assertEqual(plan(story,{"offsets":[0,1.0]})["scenes"][0]["kind"],"generic")

if __name__=="__main__":
    unittest.main()
