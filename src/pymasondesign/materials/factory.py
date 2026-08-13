from __future__ import annotations

from attrs import field, frozen
from pymasondesign.materials.enums import BlockMaterialType, StrengthClass, CeramicWallType
from pymasondesign.materials.block import BlockSpecification
from pymasondesign.materials.mortar import MortarSpecification
from pymasondesign.materials.grout import GroutSpecification
from pymasondesign.materials.masonry import MasonrySpecification
from pymasondesign.geometry.tolerances import is_close


@frozen
class NBR16868TableEntry:
    """Representa uma linha da tabela normativa de alvenaria estrutural da NBR 16868.

    Attributes:
        fbk: Resistência característica do bloco na área bruta em MPa.
        fa: Resistência média à compressão da argamassa aos 28 dias em MPa.
        fgk: Resistência característica à compressão do graute aos 28 dias em MPa.
        fpk: Resistência característica à compressão do prisma oco em MPa.
        fpgk: Resistência característica à compressão do prisma cheio/grauteado (fpk*) em MPa.
        strength_class: Classe do bloco de concreto ('A', 'B' ou 'C') ou None se cerâmico.
        wall_type: Tipo de parede para blocos cerâmicos (HOLLOW ou SOLID) ou None se concreto.
    """

    fbk: float = field(converter=float)
    fa: float = field(converter=float)
    fgk: float = field(converter=float)
    fpk: float = field(converter=float)
    fpgk: float = field(converter=float)
    strength_class: StrengthClass | None = field(default=None)
    wall_type: CeramicWallType | None = field(default=None)


# Tabela 1 da ABNT NBR 16868 - Blocos de Concreto
NBR16868_CONCRETE_TABLE: dict[float, NBR16868TableEntry] = {
    3.0: NBR16868TableEntry(fbk=3.0, strength_class=StrengthClass.C, fa=4.0, fgk=15.0, fpk=2.4, fpgk=4.8),
    4.0: NBR16868TableEntry(fbk=4.0, strength_class=StrengthClass.B, fa=4.0, fgk=15.0, fpk=3.2, fpgk=6.4),
    6.0: NBR16868TableEntry(fbk=6.0, strength_class=StrengthClass.B, fa=6.0, fgk=15.0, fpk=4.5, fpgk=7.9),
    8.0: NBR16868TableEntry(fbk=8.0, strength_class=StrengthClass.A, fa=6.0, fgk=20.0, fpk=6.0, fpgk=10.5),
    10.0: NBR16868TableEntry(fbk=10.0, strength_class=StrengthClass.A, fa=8.0, fgk=20.0, fpk=7.0, fpgk=12.3),
    12.0: NBR16868TableEntry(fbk=12.0, strength_class=StrengthClass.A, fa=8.0, fgk=25.0, fpk=8.4, fpgk=13.4),
    14.0: NBR16868TableEntry(fbk=14.0, strength_class=StrengthClass.A, fa=12.0, fgk=30.0, fpk=9.8, fpgk=15.7),
    16.0: NBR16868TableEntry(fbk=16.0, strength_class=StrengthClass.A, fa=12.0, fgk=30.0, fpk=10.4, fpgk=16.6),
    18.0: NBR16868TableEntry(fbk=18.0, strength_class=StrengthClass.A, fa=14.0, fgk=35.0, fpk=11.7, fpgk=18.7),
    20.0: NBR16868TableEntry(fbk=20.0, strength_class=StrengthClass.A, fa=14.0, fgk=35.0, fpk=12.0, fpgk=19.2),
    22.0: NBR16868TableEntry(fbk=22.0, strength_class=StrengthClass.A, fa=16.0, fgk=40.0, fpk=13.2, fpgk=21.1),
    24.0: NBR16868TableEntry(fbk=24.0, strength_class=StrengthClass.A, fa=16.0, fgk=40.0, fpk=14.4, fpgk=23.0),
}

# Tabela da ABNT NBR 16868 - Blocos Cerâmicos de Paredes Vazadas (HOLLOW)
NBR16868_CERAMIC_HOLLOW_TABLE: dict[float, NBR16868TableEntry] = {
    4.0: NBR16868TableEntry(fbk=4.0, wall_type=CeramicWallType.HOLLOW, fa=4.0, fgk=15.0, fpk=2.0, fpgk=3.2),
    6.0: NBR16868TableEntry(fbk=6.0, wall_type=CeramicWallType.HOLLOW, fa=6.0, fgk=15.0, fpk=3.0, fpgk=4.8),
    8.0: NBR16868TableEntry(fbk=8.0, wall_type=CeramicWallType.HOLLOW, fa=6.0, fgk=20.0, fpk=4.0, fpgk=6.4),
    10.0: NBR16868TableEntry(fbk=10.0, wall_type=CeramicWallType.HOLLOW, fa=8.0, fgk=25.0, fpk=4.5, fpgk=7.2),
    12.0: NBR16868TableEntry(fbk=12.0, wall_type=CeramicWallType.HOLLOW, fa=8.0, fgk=25.0, fpk=5.4, fpgk=8.6),
}

# Tabela da ABNT NBR 16868 - Blocos Cerâmicos de Paredes Maciças (SOLID)
NBR16868_CERAMIC_SOLID_TABLE: dict[float, NBR16868TableEntry] = {
    10.0: NBR16868TableEntry(fbk=10.0, wall_type=CeramicWallType.SOLID, fa=8.0, fgk=20.0, fpk=6.0, fpgk=9.6),
    14.0: NBR16868TableEntry(fbk=14.0, wall_type=CeramicWallType.SOLID, fa=12.0, fgk=25.0, fpk=8.4, fpgk=13.4),
    18.0: NBR16868TableEntry(fbk=18.0, wall_type=CeramicWallType.SOLID, fa=15.0, fgk=30.0, fpk=10.8, fpgk=17.3),
}


class NBR16868MasonryFactory:
    """Factory de especificação de alvenaria estrutural conforme tabelas normativas da NBR 16868."""

    @staticmethod
    def get_available_fbk(
        material: BlockMaterialType = BlockMaterialType.CONCRETE,
        wall_type: CeramicWallType = CeramicWallType.HOLLOW,
    ) -> tuple[float, ...]:
        """Retorna os valores de fbk disponíveis para o material e tipo de parede especificados."""
        if material == BlockMaterialType.CONCRETE:
            return tuple(sorted(NBR16868_CONCRETE_TABLE.keys()))
        elif material == BlockMaterialType.CERAMIC:
            table = NBR16868_CERAMIC_SOLID_TABLE if wall_type == CeramicWallType.SOLID else NBR16868_CERAMIC_HOLLOW_TABLE
            return tuple(sorted(table.keys()))
        else:
            raise NotImplementedError(f"Tabela normativa não disponível para {material}.")

    @staticmethod
    def get_entry(
        fbk: float,
        material: BlockMaterialType = BlockMaterialType.CONCRETE,
        wall_type: CeramicWallType = CeramicWallType.HOLLOW,
    ) -> NBR16868TableEntry:
        """Obtém a linha de especificação normativa correspondente ao fbk, material e tipo de parede."""
        fbk_float = float(fbk)
        if material == BlockMaterialType.CONCRETE:
            matching_key = next((k for k in NBR16868_CONCRETE_TABLE if is_close(k, fbk_float)), None)
            if matching_key is None:
                available = list(NBR16868_CONCRETE_TABLE.keys())
                raise KeyError(f"fbk={fbk} MPa não encontrado para blocos de concreto. Disponíveis: {available}")
            return NBR16868_CONCRETE_TABLE[matching_key]
        elif material == BlockMaterialType.CERAMIC:
            table = NBR16868_CERAMIC_SOLID_TABLE if wall_type == CeramicWallType.SOLID else NBR16868_CERAMIC_HOLLOW_TABLE
            matching_key = next((k for k in table if is_close(k, fbk_float)), None)
            if matching_key is None:
                available = list(table.keys())
                tipo = "maciça" if wall_type == CeramicWallType.SOLID else "vazada"
                raise KeyError(f"fbk={fbk} MPa não encontrado para blocos cerâmicos de parede {tipo}. Disponíveis: {available}")
            return table[matching_key]
        else:
            raise NotImplementedError(f"Tabela normativa não disponível para {material}.")

    @staticmethod
    def create(
        fbk: float,
        material: BlockMaterialType = BlockMaterialType.CONCRETE,
        wall_type: CeramicWallType = CeramicWallType.HOLLOW,
        transverse_joints_filled: bool = True,
        elastic_modulus: float | None = None,
    ) -> MasonrySpecification:
        """Cria uma instância de MasonrySpecification calibrada pela tabela da NBR 16868 para blocos de concreto ou cerâmicos.

        Args:
            fbk: Resistência do bloco na área bruta em MPa.
            material: Tipo do material (CONCRETE ou CERAMIC).
            wall_type: Tipo de parede para blocos cerâmicos (HOLLOW ou SOLID).
            transverse_joints_filled: Se True, juntas transversais preenchidas (fator 1.0); se False, 0.8.
            elastic_modulus: Módulo Em explícito opcional. Se None, calculado por fbk.

        Returns:
            Instância calibrada de MasonrySpecification.
        """
        entry = NBR16868MasonryFactory.get_entry(fbk=fbk, material=material, wall_type=wall_type)

        if material == BlockMaterialType.CONCRETE:
            block = BlockSpecification.concrete(fbk=entry.fbk, strength_class=entry.strength_class or StrengthClass.A)
        else:
            block = BlockSpecification.ceramic(fbk=entry.fbk, wall_type=entry.wall_type or CeramicWallType.HOLLOW)

        mortar = MortarSpecification(fa=entry.fa)
        grout = GroutSpecification(fg=entry.fgk)

        return MasonrySpecification(
            block=block,
            mortar=mortar,
            grout=grout,
            fpk=entry.fpk,
            fpgk=entry.fpgk,
            transverse_joints_filled=transverse_joints_filled,
            elastic_modulus=elastic_modulus,
        )
