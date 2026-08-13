from __future__ import annotations

import unittest
from pymasondesign.materials import (
    SteelCategory,
    BlockMaterialType,
    StrengthClass,
    CeramicWallType,
    SteelSpecification,
    BlockSpecification,
    MortarSpecification,
    GroutSpecification,
    MasonrySpecification,
    NBR16868TableEntry,
    NBR16868MasonryFactory,
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

    def test_nbr16868_factory_all_table_entries(self):
        # 1. Verifica os 12 valores disponíveis
        available = NBR16868MasonryFactory.get_available_fbk()
        expected_fbk = (3.0, 4.0, 6.0, 8.0, 10.0, 12.0, 14.0, 16.0, 18.0, 20.0, 22.0, 24.0)
        self.assertEqual(available, expected_fbk)

        # 2. Teste específico para fbk = 14 MPa (Classe A, fa=12, fg=30, fpk=9.8, fpgk=15.7)
        entry14 = NBR16868MasonryFactory.get_entry(14.0)
        self.assertEqual(entry14.strength_class, StrengthClass.A)
        self.assertAlmostEqual(entry14.fa, 12.0)
        self.assertAlmostEqual(entry14.fgk, 30.0)
        self.assertAlmostEqual(entry14.fpk, 9.8)
        self.assertAlmostEqual(entry14.fpgk, 15.7)

        # 3. Teste do método de fábrica na MasonrySpecification
        m14 = MasonrySpecification.from_nbr16868(fbk=14.0)
        self.assertAlmostEqual(m14.block.fbk, 14.0)
        self.assertEqual(m14.block.strength_class, StrengthClass.A)
        self.assertAlmostEqual(m14.mortar.fa, 12.0)
        self.assertAlmostEqual(m14.grout.fg, 30.0)
        self.assertAlmostEqual(m14.fpk, 9.8)
        self.assertAlmostEqual(m14.fpgk, 15.7)
        self.assertAlmostEqual(m14.fk_hollow, 0.70 * 9.8)
        self.assertAlmostEqual(m14.fk_grouted, 0.70 * 15.7)

        # 4. Classes C (fbk=3) e B (fbk=4)
        entry3 = NBR16868MasonryFactory.get_entry(3.0)
        self.assertEqual(entry3.strength_class, StrengthClass.C)
        entry4 = NBR16868MasonryFactory.get_entry(4.0)
        self.assertEqual(entry4.strength_class, StrengthClass.B)

        # 5. fbk com pequena variação de ponto flutuante é aceito via tolerância
        entry14_float = NBR16868MasonryFactory.get_entry(14.00000000001)
        self.assertAlmostEqual(entry14_float.fbk, 14.0)

        # 6. fbk inválido dispara KeyError
        with self.assertRaises(KeyError):
            NBR16868MasonryFactory.get_entry(99.0)

    def test_nbr16868_ceramic_tables(self):
        # 1. Cerâmico - Paredes Vazadas (fbk = 4, 6, 8, 10, 12)
        hollow_fbk = NBR16868MasonryFactory.get_available_fbk(
            material=BlockMaterialType.CERAMIC, wall_type=CeramicWallType.HOLLOW
        )
        self.assertEqual(hollow_fbk, (4.0, 6.0, 8.0, 10.0, 12.0))

        entry_hollow_10 = NBR16868MasonryFactory.get_entry(
            fbk=10.0, material=BlockMaterialType.CERAMIC, wall_type=CeramicWallType.HOLLOW
        )
        self.assertEqual(entry_hollow_10.wall_type, CeramicWallType.HOLLOW)
        self.assertAlmostEqual(entry_hollow_10.fa, 8.0)
        self.assertAlmostEqual(entry_hollow_10.fgk, 25.0)
        self.assertAlmostEqual(entry_hollow_10.fpk, 4.5)
        self.assertAlmostEqual(entry_hollow_10.fpgk, 7.2)

        # 2. Cerâmico - Paredes Maciças (fbk = 10, 14, 18)
        solid_fbk = NBR16868MasonryFactory.get_available_fbk(
            material=BlockMaterialType.CERAMIC, wall_type=CeramicWallType.SOLID
        )
        self.assertEqual(solid_fbk, (10.0, 14.0, 18.0))

        entry_solid_18 = NBR16868MasonryFactory.get_entry(
            fbk=18.0, material=BlockMaterialType.CERAMIC, wall_type=CeramicWallType.SOLID
        )
        self.assertEqual(entry_solid_18.wall_type, CeramicWallType.SOLID)
        self.assertAlmostEqual(entry_solid_18.fa, 15.0)
        self.assertAlmostEqual(entry_solid_18.fgk, 30.0)
        self.assertAlmostEqual(entry_solid_18.fpk, 10.8)
        self.assertAlmostEqual(entry_solid_18.fpgk, 17.3)

        # 3. Factory method from_nbr16868 para cerâmicos
        m_cer_solid = MasonrySpecification.from_nbr16868(
            fbk=14.0,
            material=BlockMaterialType.CERAMIC,
            wall_type=CeramicWallType.SOLID,
        )
        self.assertEqual(m_cer_solid.block.material, BlockMaterialType.CERAMIC)
        self.assertEqual(m_cer_solid.block.wall_type, CeramicWallType.SOLID)
        self.assertAlmostEqual(m_cer_solid.block.fbk, 14.0)
        self.assertAlmostEqual(m_cer_solid.mortar.fa, 12.0)
        self.assertAlmostEqual(m_cer_solid.grout.fg, 25.0)
        self.assertAlmostEqual(m_cer_solid.fpk, 8.4)
        self.assertAlmostEqual(m_cer_solid.fpgk, 13.4)


if __name__ == "__main__":
    unittest.main()
