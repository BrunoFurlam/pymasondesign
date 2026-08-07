from __future__ import annotations

import unittest
from pymasondesign.mechanics import SectionForces


class TestSectionForces(unittest.TestCase):
    def test_default_values(self):
        forces = SectionForces()
        self.assertEqual(forces.normal, 0.0)
        self.assertEqual(forces.moment_x, 0.0)
        self.assertEqual(forces.moment_y, 0.0)
        self.assertEqual(forces.shear_x, 0.0)
        self.assertEqual(forces.shear_y, 0.0)
        self.assertEqual(forces.torsion, 0.0)

    def test_custom_values(self):
        forces = SectionForces(
            normal=-150.0,
            moment_x=3200.0,
            moment_y=1800.0,
            shear_x=45.0,
            shear_y=12.0,
            torsion=5.0,
        )
        self.assertEqual(forces.normal, -150.0)
        self.assertEqual(forces.moment_x, 3200.0)
        self.assertEqual(forces.moment_y, 1800.0)
        self.assertEqual(forces.shear_x, 45.0)
        self.assertEqual(forces.shear_y, 12.0)
        self.assertEqual(forces.torsion, 5.0)

    def test_scale_and_multiplication(self):
        forces = SectionForces(normal=-100.0, moment_x=200.0, shear_x=10.0)
        scaled = forces.scale(1.4)

        self.assertAlmostEqual(scaled.normal, -140.0)
        self.assertAlmostEqual(scaled.moment_x, 280.0)
        self.assertAlmostEqual(scaled.shear_x, 14.0)

        # Operador de multiplicação
        scaled_op = forces * 1.4
        self.assertAlmostEqual(scaled_op.normal, -140.0)

        # Multiplicação reversa (1.4 * forces)
        scaled_rop = 1.4 * forces
        self.assertAlmostEqual(scaled_rop.normal, -140.0)

    def test_addition(self):
        f1 = SectionForces(normal=-100.0, moment_x=500.0, shear_x=20.0)
        f2 = SectionForces(normal=-50.0, moment_x=300.0, shear_x=15.0, torsion=2.0)
        f_total = f1 + f2

        self.assertAlmostEqual(f_total.normal, -150.0)
        self.assertAlmostEqual(f_total.moment_x, 800.0)
        self.assertAlmostEqual(f_total.shear_x, 35.0)
        self.assertAlmostEqual(f_total.torsion, 2.0)

    def test_combine_from_iterable(self):
        forces_list = [
            SectionForces(normal=-100.0, moment_x=200.0, shear_x=10.0),
            SectionForces(normal=-50.0, moment_y=150.0, shear_y=5.0),
            SectionForces(normal=20.0, moment_x=-50.0, torsion=3.0),
        ]
        combined = SectionForces.combine(forces_list)

        self.assertAlmostEqual(combined.normal, -130.0)
        self.assertAlmostEqual(combined.moment_x, 150.0)
        self.assertAlmostEqual(combined.moment_y, 150.0)
        self.assertAlmostEqual(combined.shear_x, 10.0)
        self.assertAlmostEqual(combined.shear_y, 5.0)
        self.assertAlmostEqual(combined.torsion, 3.0)

        # Teste com gerador / iterador vazio
        empty_combined = SectionForces.combine([])
        self.assertEqual(empty_combined, SectionForces())


if __name__ == "__main__":
    unittest.main()
