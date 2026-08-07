from pymasondesign.sections.base import Section
from pymasondesign.sections.properties import SectionProperties
from pymasondesign.mechanics.forces import SectionForces
from pymasondesign.mechanics.stress_plane import NormalStressPlane
from pymasondesign.mechanics.enums import StressRegime

# Constante de tolerância numérica padrão para esforços e verificações
DEFAULT_TOLERANCE: float = 1e-6


class MechanicsService:
    """Serviço estático e funcional para execução dos principais cálculos da mecânica das estruturas."""

    @staticmethod
    def integrate_normal_stress(
        plane: NormalStressPlane,
        section: Section,
    ) -> float:
        """Calcula a força normal acumulada (integral de σ(x, y) dA) sobre uma seção ou polígono.

        Como o plano de tensões é afim/linear σ(x, y) = c0 + cx * x + cy * y,
        o Teorema da Média fornece analiticamente o valor exato:
            N = A * σ(x_cg, y_cg)
        onde (x_cg, y_cg) é o centro de gravidade da região integrada no mesmo sistema do plano.

        Args:
            plane: Plano linear de tensões normais.
            section: Seção (polígono, retângulo, seção composta) sobre a qual integrar a tensão.

        Returns:
            Força normal total acumulada na área da seção.
        """
        props = section.compute_properties()
        sigma_at_cg = plane.stress_at(props.cg.x, props.cg.y)
        return props.area * sigma_at_cg

    @staticmethod
    def calculate_accumulated_force(
        plane: NormalStressPlane,
        section: Section,
    ) -> float:
        """Alias para integrate_normal_stress."""
        return MechanicsService.integrate_normal_stress(plane, section)

    @staticmethod
    def calculate_normal_stress_plane(
        forces: SectionForces,
        properties: SectionProperties,
    ) -> NormalStressPlane:
        """Calcula o plano linear de tensões normais (NormalStressPlane) a partir dos esforços e da geometria.

        Aplica a formulação geral da flexo-compressão biaxial oblíqua:
            c0 = N / A
            cx = (My * Ixx - Mx * Ixy) / D
            cy = (Mx * Iyy - My * Ixy) / D
        onde D = Ixx * Iyy - Ixy^2.
        """
        if properties.area <= 0:
            raise ValueError(f"A área da seção deve ser estritamente positiva, obtido: {properties.area}.")

        c0 = forces.normal / properties.area

        det = properties.ixx * properties.iyy - properties.ixy**2
        if det == 0:
            if forces.moment_x != 0.0 or forces.moment_y != 0.0:
                raise ZeroDivisionError("Determinante dos momentos de inércia é nulo para momentos não-nulos.")
            cx = 0.0
            cy = 0.0
        else:
            cx = (forces.moment_y * properties.ixx - forces.moment_x * properties.ixy) / det
            cy = (forces.moment_x * properties.iyy - forces.moment_y * properties.ixy) / det

        return NormalStressPlane(c0=c0, cx=cx, cy=cy)

    @staticmethod
    def calculate_eccentricities(forces: SectionForces) -> tuple[float, float]:
        """Calcula as excentricidades de 1ª ordem da carga normal: (ex, ey) = (|My| / |N|, |Mx| / |N|).

        Returns:
            Tupla (ex, ey). Se N for nulo, retorna (inf, inf) caso haja momentos ou (0.0, 0.0).
        """
        abs_n = abs(forces.normal)
        if abs_n <= DEFAULT_TOLERANCE:
            ex = float("inf") if abs(forces.moment_y) > DEFAULT_TOLERANCE else 0.0
            ey = float("inf") if abs(forces.moment_x) > DEFAULT_TOLERANCE else 0.0
            return ex, ey

        ex = abs(forces.moment_y) / abs_n
        ey = abs(forces.moment_x) / abs_n
        return ex, ey

    @staticmethod
    def calculate_extreme_stresses(
        plane: NormalStressPlane,
        properties: SectionProperties,
    ) -> tuple[float, float]:
        """Calcula as tensões normais extremas (sigma_min, sigma_max) nos quatro cantos dos limites da seção.

        Returns:
            Tupla contendo (sigma_min, sigma_max).
        """
        cg_x = properties.cg.x
        cg_y = properties.cg.y

        # Coordenadas relativas dos 4 cantos do BoundingBox
        corners_rel = [
            (properties.bounds.xmin - cg_x, properties.bounds.ymin - cg_y),
            (properties.bounds.xmax - cg_x, properties.bounds.ymin - cg_y),
            (properties.bounds.xmax - cg_x, properties.bounds.ymax - cg_y),
            (properties.bounds.xmin - cg_x, properties.bounds.ymax - cg_y),
        ]

        stresses = [plane.stress_at(x_rel, y_rel) for x_rel, y_rel in corners_rel]
        return min(stresses), max(stresses)

    @staticmethod
    def classify_stress_regime(forces: SectionForces) -> StressRegime:
        """Classifica o regime de esforço e flexão atuante na seção transversal."""
        has_n = abs(forces.normal) > DEFAULT_TOLERANCE
        has_mx = abs(forces.moment_x) > DEFAULT_TOLERANCE
        has_my = abs(forces.moment_y) > DEFAULT_TOLERANCE

        if not has_n and not has_mx and not has_my:
            return StressRegime.NO_LOAD

        if not has_mx and not has_my:
            return StressRegime.PURE_COMPRESSION if forces.normal < 0 else StressRegime.PURE_TENSION

        if not has_n:
            if has_mx and has_my:
                return StressRegime.PURE_BENDING_XY
            return StressRegime.PURE_BENDING_X if has_mx else StressRegime.PURE_BENDING_Y

        # Com esforço normal presente
        if forces.normal < 0:
            if has_mx and has_my:
                return StressRegime.FLEXO_COMPRESSION_XY
            return StressRegime.FLEXO_COMPRESSION_X if has_mx else StressRegime.FLEXO_COMPRESSION_Y
        else:
            if has_mx and has_my:
                return StressRegime.FLEXO_TENSION_XY
            return StressRegime.FLEXO_TENSION_X if has_mx else StressRegime.FLEXO_TENSION_Y
