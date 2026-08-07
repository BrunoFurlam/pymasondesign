from __future__ import annotations

import unittest
from pymasondesign.materials import (
    SteelCategory,
    BlockMaterialType,
    SteelSpecification,
    BlockSpecification,
    MortarSpecification,
    GroutSpecification,
    MasonrySpecification,
)


class TestMaterials(unittest.TestCase):
    def test_steel_specification(self):
        steel_ca50 = SteelSpecification.ca50()
        self.assertEqual(steel_ca50.category, SteelCategory.CA50)
        self.assertAlmostEqual(steel_ca50.fyk, 500.0)
        self.assertAlmostEqual(steel_ca50.es, 210000.0)

        # fyd com gamma_s = 1.15
        fyd = steel_ca50.calculate_fyd(gamma_s=1.15)
        self.assertAlmostEqual(fyd, 500.0 / 1.15)

        # fyd com fração de 50% de fyk (ex: blocos cerâmicos ou análise específica)
        fyd_half = steel_ca50.calculate_fyd(gamma_s=1.15, fyk_fraction=0.50)
        self.assertAlmostEqual(fyd_half, 250.0 / 1.15)

        # eyd com gamma_s = 1.15 e fração de 50%
        eyd_half = steel_ca50.calculate_eyd(gamma_s=1.15, fyk_fraction=0.50)
        self.assertAlmostEqual(eyd_half, (250.0 / 1.15) / 210000.0)

        # Validação de fyk_fraction inválido
        with self.assertRaises(ValueError):
            steel_ca50.calculate_fyd(gamma_s=1.15, fyk_fraction=0.0)
        with self.assertRaises(ValueError):
            steel_ca50.calculate_fyd(gamma_s=1.15, fyk_fraction=1.2)

        # CA60
        steel_ca60 = SteelSpecification.ca60()
        self.assertEqual(steel_ca60.category, SteelCategory.CA60)
        self.assertAlmostEqual(steel_ca60.calculate_fyd(gamma_s=1.15), 600.0 / 1.15)

    def test_block_mortar_grout_specifications(self):
        block = BlockSpecification.concrete(fbk=14.0)
        self.assertEqual(block.material, BlockMaterialType.CONCRETE)
        self.assertAlmostEqual(block.fbk, 14.0)

        mortar = MortarSpecification(fa=8.0)
        self.assertAlmostEqual(mortar.fa, 8.0)

        grout = GroutSpecification(fg=25.0)
        self.assertAlmostEqual(grout.fg, 25.0)

        with self.assertRaises(ValueError):
            BlockSpecification(fbk=-5.0)
        with self.assertRaises(ValueError):
            MortarSpecification(fa=0.0)
        with self.assertRaises(ValueError):
            GroutSpecification(fg=-1.0)

    def test_masonry_elastic_modulus_stepping_by_fbk(self):
        mortar = MortarSpecification(fa=8.0)
        grout = GroutSpecification(fg=20.0)

        # fbk <= 20 MPa -> Em = 800 * fpk
        m1 = MasonrySpecification(
            block=BlockSpecification.concrete(fbk=14.0),
            mortar=mortar,
            grout=grout,
            fpk=10.0,
            fpgk=16.0,
        )
        self.assertAlmostEqual(m1.em, 800.0 * 10.0)

        # 20 < fbk < 26 MPa (ex: 22 e 24 MPa) -> Em = 750 * fpk
        m2 = MasonrySpecification(
            block=BlockSpecification.concrete(fbk=22.0),
            mortar=mortar,
            grout=grout,
            fpk=15.0,
            fpgk=22.0,
        )
        self.assertAlmostEqual(m2.em, 750.0 * 15.0)

        # fbk >= 26 MPa -> Em = 700 * fpk
        m3 = MasonrySpecification(
            block=BlockSpecification.concrete(fbk=28.0),
            mortar=mortar,
            grout=grout,
            fpk=20.0,
            fpgk=28.0,
        )
        self.assertAlmostEqual(m3.em, 700.0 * 20.0)

        # Custom explicit Em
        m_custom = MasonrySpecification(
            block=BlockSpecification.concrete(fbk=14.0),
            mortar=mortar,
            grout=grout,
            fpk=10.0,
            fpgk=16.0,
            elastic_modulus=12345.0,
        )
        self.assertAlmostEqual(m_custom.em, 12345.0)

    def test_masonry_transverse_joints_and_linear_grout_interpolation(self):
        block = BlockSpecification.concrete(fbk=14.0)
        mortar = MortarSpecification(fa=8.0)
        grout = GroutSpecification(fg=20.0)

        # 1. Juntas transversais preenchidas (eta_j = 1.0)
        m_filled = MasonrySpecification(
            block=block,
            mortar=mortar,
            grout=grout,
            fpk=10.0,
            fpgk=18.0,
            transverse_joints_filled=True,
        )
        self.assertAlmostEqual(m_filled.fk_hollow, 0.70 * 10.0)  # 7.0 MPa
        self.assertAlmostEqual(m_filled.fk_grouted, 0.70 * 18.0)  # 12.6 MPa

        # Interpolação linear de fk pela taxa de grauteamento rho_g
        self.assertAlmostEqual(m_filled.calculate_fk(grout_ratio=0.0), 7.0)
        self.assertAlmostEqual(m_filled.calculate_fk(grout_ratio=1.0), 12.6)
        self.assertAlmostEqual(m_filled.calculate_fk(grout_ratio=0.5), 0.5 * 7.0 + 0.5 * 12.6)  # 9.8 MPa

        # Resistência de cálculo fd com gamma_m = 1.40
        fd_50 = m_filled.calculate_fd(gamma_m=1.40, grout_ratio=0.5)
        self.assertAlmostEqual(fd_50, 9.8 / 1.40)

        # 2. Juntas transversais não preenchidas (eta_j = 0.80)
        m_unfilled = MasonrySpecification(
            block=block,
            mortar=mortar,
            grout=grout,
            fpk=10.0,
            fpgk=18.0,
            transverse_joints_filled=False,
        )
        self.assertAlmostEqual(m_unfilled.fk_hollow, 0.70 * 0.80 * 10.0)  # 5.6 MPa
        self.assertAlmostEqual(m_unfilled.fk_grouted, 0.70 * 0.80 * 18.0)  # 10.08 MPa
        self.assertAlmostEqual(m_unfilled.calculate_fk(grout_ratio=0.5), 0.5 * 5.6 + 0.5 * 10.08)  # 7.84 MPa


if __name__ == "__main__":
    unittest.main()
