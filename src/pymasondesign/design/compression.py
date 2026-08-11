from __future__ import annotations

import math
from attrs import field, frozen
from pymasondesign.common import to_tuple
from pymasondesign.geometry.tolerances import GEOMETRIC_TOLERANCE, is_close, is_zero
from pymasondesign.sections.properties import SectionProperties
from pymasondesign.materials.masonry import MasonrySpecification
from pymasondesign.mechanics.forces import SectionForces
from pymasondesign.mechanics.stress_plane import NormalStressPlane
from pymasondesign.mechanics.enums import StressRegime
from pymasondesign.mechanics.service import MechanicsService
from pymasondesign.design.section import ResistantSection
from pymasondesign.design.segment import ResistantSegment
from pymasondesign.design.grouting import (
    GroutInterval,
    SegmentGroutDemand,
    SectionGroutDemand,
)


@frozen
class CompressionDesignOptions:
    """Configurações e coeficientes para o dimensionamento e verificação à flexo-compressão (NBR 16868-1).

    Attributes:
        gamma_m: Coeficiente de minoração da resistência da alvenaria (padrão 2.00 para alvenaria não armada).
        k_flexure: Fator de correção da compressão na flexão na distribuição linear de tensões (padrão 1.50).
        max_slenderness: Limite normativo máximo de esbeltez da parede/seção (padrão 24.0 conforme NBR 16868-1).
        max_interval_length: Comprimento máximo para subdivisão de trechos de grauteamento (em cm ou m). Se None, trechos contínuos integrais.
    """

    gamma_m: float = field(default=2.0, converter=float)
    k_flexure: float = field(default=1.5, converter=float)
    max_slenderness: float = field(default=24.0, converter=float)
    max_interval_length: float | None = field(default=None)

    def __attrs_post_init__(self) -> None:
        if self.gamma_m <= 0:
            raise ValueError(f"gamma_m deve ser estritamente positivo, obtido: {self.gamma_m}.")
        if self.k_flexure <= 0:
            raise ValueError(f"k_flexure deve ser estritamente positivo, obtido: {self.k_flexure}.")
        if self.max_slenderness <= 0:
            raise ValueError(f"max_slenderness deve ser estritamente positivo, obtido: {self.max_slenderness}.")
        if self.max_interval_length is not None and self.max_interval_length <= 0:
            raise ValueError(
                f"max_interval_length deve ser positivo se fornecido, obtido: {self.max_interval_length}."
            )


@frozen
class CompressionDesignResult:
    """Resultado detalhado do dimensionamento à flexo-compressão de uma seção resistente.

    Attributes:
        section: Seção resistente dimensionada.
        forces: Esforços solicitantes atuantes.
        masonry_spec: Especificação de alvenaria adotada.
        options: Opções de dimensionamento empregadas.
        slenderness: Índice de esbeltez calculado (lambda = h_ef / t_ef).
        slenderness_reduction_factor: Fator redutor de esbeltez (R = 1 - (lambda/40)^3).
        grout_demand: Demanda de grauteamento calculada por trecho ao longo de todos os segmentos.
        max_equivalent_compressive_stress: Pico de tensão equivalente de compressão (em magnitude positiva).
        max_equivalent_tensile_stress: Pico de tensão equivalente de tração.
        max_allowable_stress: Tensão máxima admissível da alvenaria (f_d totalmente grauteada).
        utilization_ratio: Taxa máxima de utilização da seção (sigma_max / f_d_max).
        is_feasible: True se a esbeltez for <= 24 e o grauteamento máximo (100%) for suficiente para absorver as tensões.
        stress_regime: Regime de tensões atuante na seção.
    """

    section: ResistantSection = field()
    forces: SectionForces = field()
    masonry_spec: MasonrySpecification = field()
    options: CompressionDesignOptions = field()
    slenderness: float = field(converter=float)
    slenderness_reduction_factor: float = field(converter=float)
    grout_demand: SectionGroutDemand = field()
    max_equivalent_compressive_stress: float = field(converter=float)
    max_equivalent_tensile_stress: float = field(converter=float)
    max_allowable_stress: float = field(converter=float)
    utilization_ratio: float = field(converter=float)
    is_feasible: bool = field()
    stress_regime: StressRegime = field()

    @property
    def section_id(self) -> str:
        """Identificador da seção resistente analisada."""
        return self.section.section_id

    @property
    def is_slenderness_ok(self) -> bool:
        """Indica se a esbeltez atende ao limite normativo."""
        return self.slenderness <= self.options.max_slenderness


@frozen
class CompressionVerificationResult:
    """Resultado da verificação normativa de flexo-compressão para uma seção com grauteamento definido.

    Attributes:
        section: Seção resistente verificada.
        forces: Esforços solicitantes atuantes.
        masonry_spec: Especificação de alvenaria.
        grout_demand: Perfil de grauteamento considerado na verificação.
        options: Opções de verificação.
        slenderness: Índice de esbeltez (lambda).
        slenderness_reduction_factor: Fator redutor de esbeltez (R).
        max_equivalent_compressive_stress: Tensão equivalente máxima de compressão atuante.
        allowable_stress: Tensão de cálculo resistente correspondente.
        utilization_ratio: Razão de utilização (tensão atuante / tensão resistente).
        is_verified: True se a seção atende integralmente à esbeltez e às tensões admissíveis.
        slenderness_ok: True se lambda <= max_slenderness.
        stress_ok: True se a tensão atuante for <= resistência de cálculo em todos os pontos.
        stress_regime: Regime de tensões atuante.
    """

    section: ResistantSection = field()
    forces: SectionForces = field()
    masonry_spec: MasonrySpecification = field()
    grout_demand: SectionGroutDemand = field()
    options: CompressionDesignOptions = field()
    slenderness: float = field(converter=float)
    slenderness_reduction_factor: float = field(converter=float)
    max_equivalent_compressive_stress: float = field(converter=float)
    allowable_stress: float = field(converter=float)
    utilization_ratio: float = field(converter=float)
    is_verified: bool = field()
    slenderness_ok: bool = field()
    stress_ok: bool = field()
    stress_regime: StressRegime = field()

    @property
    def section_id(self) -> str:
        """Identificador da seção resistente."""
        return self.section.section_id


class CompressionDesignService:
    """Serviço de domínio para dimensionamento e verificação à compressão e flexo-compressão (NBR 16868-1)."""

    @staticmethod
    def calculate_slenderness(height: float, thickness: float) -> float:
        """Calcula o índice de esbeltez da parede/seção: lambda = h_ef / t_ef."""
        if thickness <= 0:
            raise ValueError(f"Espessura deve ser positiva, obtido: {thickness}.")
        if height <= 0:
            raise ValueError(f"Altura deve ser positiva, obtido: {height}.")
        return height / thickness

    @staticmethod
    def calculate_reduction_factor(height: float, thickness: float) -> float:
        """Calcula o fator redutor de esbeltez: R = 1 - (lambda / 40)^3."""
        slenderness = CompressionDesignService.calculate_slenderness(height, thickness)
        factor = 1.0 - (slenderness / 40.0) ** 3
        return max(factor, 0.0)

    @staticmethod
    def calculate_equivalent_stress_plane(
        forces: SectionForces,
        properties: SectionProperties,
        r_factor: float,
        k_flexure: float,
    ) -> NormalStressPlane:
        """Gera o plano linear de tensões equivalentes de cálculo da flexo-compressão (NBR 16868-1).

        Equação normativa:
            sigma_eq(x, y) = c0 / R + (cx * x + cy * y) / K
        """
        raw_plane = MechanicsService.calculate_normal_stress_plane(forces, properties)
        c0_eq = raw_plane.c0 / r_factor if r_factor > 0 else raw_plane.c0
        cx_eq = raw_plane.cx / k_flexure
        cy_eq = raw_plane.cy / k_flexure
        return NormalStressPlane(c0=c0_eq, cx=cx_eq, cy=cy_eq)

    @classmethod
    def design_grouting_demand(
        cls,
        section: ResistantSection,
        forces: SectionForces,
        masonry_spec: MasonrySpecification,
        options: CompressionDesignOptions | None = None,
    ) -> CompressionDesignResult:
        """Dimensiona a demanda de grauteamento necessária para resistir à flexo-compressão da seção resistente.

        Args:
            section: Seção resistente contendo os segmentos estruturais.
            forces: Esforços solicitantes atuantes na seção.
            masonry_spec: Especificação mecânica da alvenaria (blocos, graute, prisma).
            options: Opções de cálculo (coeficientes gamma_m, K, limite de esbeltez e tamanho máximo de trecho).

        Returns:
            CompressionDesignResult com a SectionGroutDemand detalhada por trecho e status de viabilidade.
        """
        opts = options or CompressionDesignOptions()

        # 1. Análise de Esbeltez (baseada na menor espessura entre os segmentos)
        t_ef = min(seg.thickness for seg in section.segments)
        slenderness = cls.calculate_slenderness(section.height, t_ef)
        r_factor = cls.calculate_reduction_factor(section.height, t_ef)
        slenderness_ok = (slenderness <= opts.max_slenderness) and (r_factor > 0.0)

        # 2. Plano de Tensões Equivalentes
        r_eff = r_factor if r_factor > 0.0 else 1.0
        eq_plane = cls.calculate_equivalent_stress_plane(
            forces=forces,
            properties=section.properties,
            r_factor=r_eff,
            k_flexure=opts.k_flexure,
        )

        stress_regime = MechanicsService.classify_stress_regime(forces)

        # 3. Resistências de Cálculo da Alvenaria
        fd_hollow = masonry_spec.fk_hollow / opts.gamma_m
        fd_grouted = masonry_spec.fk_grouted / opts.gamma_m
        delta_fd = fd_grouted - fd_hollow

        any_infeasible = not slenderness_ok
        segment_demands: list[SegmentGroutDemand] = []

        # 4. Determinação de trechos comprimidos e taxa de graute por segmento
        for seg in section.segments:
            p_start = seg.local_axis.start
            p_end = seg.local_axis.end
            l_seg = seg.effective_length

            sig_start = eq_plane.stress_at(p_start.x, p_start.y)
            sig_end = eq_plane.stress_at(p_end.x, p_end.y)

            # Identificação de regiões base (COMP = compressão sig < 0, TENS = tração/nulo sig >= 0)
            base_spans: list[tuple[float, float, str]] = []

            # Verifica se há cruzamento com a Linha Neutra (sig = 0)
            if sig_start < -GEOMETRIC_TOLERANCE and sig_end < -GEOMETRIC_TOLERANCE:
                base_spans.append((0.0, l_seg, "COMP"))
            elif sig_start >= -GEOMETRIC_TOLERANCE and sig_end >= -GEOMETRIC_TOLERANCE:
                base_spans.append((0.0, l_seg, "TENS"))
            else:
                # Interpolação linear da posição da linha neutra no segmento
                s_zero = (-sig_start) / (sig_end - sig_start) * l_seg
                s_zero = max(0.0, min(l_seg, s_zero))

                if sig_start < 0:
                    base_spans.append((0.0, s_zero, "COMP"))
                    base_spans.append((s_zero, l_seg, "TENS"))
                else:
                    base_spans.append((0.0, s_zero, "TENS"))
                    base_spans.append((s_zero, l_seg, "COMP"))

            # Subdivisão por max_interval_length se aplicável
            sub_spans: list[tuple[float, float, str]] = []
            for s_a, s_b, kind in base_spans:
                span_len = s_b - s_a
                if span_len <= GEOMETRIC_TOLERANCE:
                    continue

                if (
                    kind == "TENS"
                    or opts.max_interval_length is None
                    or span_len <= opts.max_interval_length
                ):
                    sub_spans.append((s_a, s_b, kind))
                else:
                    n_sub = math.ceil(span_len / opts.max_interval_length)
                    d_s = span_len / n_sub
                    for i in range(n_sub):
                        sub_start = s_a + i * d_s
                        sub_end = s_b if i == n_sub - 1 else (s_a + (i + 1) * d_s)
                        sub_spans.append((sub_start, sub_end, kind))

            # Cálculo da taxa de graute para cada subintervalo
            intervals: list[GroutInterval] = []
            for sub_start, sub_end, kind in sub_spans:
                if kind == "TENS":
                    ratio = 0.0
                else:
                    # Avalia as tensões nos extremos do subintervalo
                    t_a = sub_start / l_seg
                    t_b = sub_end / l_seg
                    pt_a_x = p_start.x + t_a * (p_end.x - p_start.x)
                    pt_a_y = p_start.y + t_a * (p_end.y - p_start.y)
                    pt_b_x = p_start.x + t_b * (p_end.x - p_start.x)
                    pt_b_y = p_start.y + t_b * (p_end.y - p_start.y)

                    sig_a = eq_plane.stress_at(pt_a_x, pt_a_y)
                    sig_b = eq_plane.stress_at(pt_b_x, pt_b_y)

                    # Pico de tensão de compressão no subintervalo (magnitude positiva)
                    comp_peak = max(-sig_a, -sig_b, 0.0)

                    if comp_peak <= fd_hollow + GEOMETRIC_TOLERANCE:
                        ratio = 0.0
                    else:
                        if delta_fd > GEOMETRIC_TOLERANCE:
                            raw_ratio = (comp_peak - fd_hollow) / delta_fd
                        else:
                            raw_ratio = 1.0 if comp_peak > fd_hollow else 0.0

                        if raw_ratio > 1.0 + GEOMETRIC_TOLERANCE:
                            any_infeasible = True

                        ratio = min(max(raw_ratio, 0.0), 1.0)

                intervals.append(
                    GroutInterval(
                        start_offset=sub_start,
                        end_offset=sub_end,
                        ratio=ratio,
                    )
                )

            segment_demands.append(
                SegmentGroutDemand(
                    segment_id=seg.segment_id,
                    effective_length=l_seg,
                    intervals=tuple(intervals),
                )
            )

        section_demand = SectionGroutDemand(
            section_id=section.section_id,
            segment_demands=tuple(segment_demands),
        )

        # 5. Tensões extremas e taxa de utilização
        min_stress, max_stress = MechanicsService.calculate_extreme_stresses(
            eq_plane, section.properties
        )
        max_comp = max(-min_stress, 0.0)
        max_tens = max(max_stress, 0.0)

        utilization = max_comp / fd_grouted if fd_grouted > 0 else 0.0
        is_feasible = (not any_infeasible) and (max_comp <= fd_grouted + GEOMETRIC_TOLERANCE)

        return CompressionDesignResult(
            section=section,
            forces=forces,
            masonry_spec=masonry_spec,
            options=opts,
            slenderness=slenderness,
            slenderness_reduction_factor=r_factor,
            grout_demand=section_demand,
            max_equivalent_compressive_stress=max_comp,
            max_equivalent_tensile_stress=max_tens,
            max_allowable_stress=fd_grouted,
            utilization_ratio=utilization,
            is_feasible=is_feasible,
            stress_regime=stress_regime,
        )

    @classmethod
    def verify_section(
        cls,
        section: ResistantSection,
        forces: SectionForces,
        masonry_spec: MasonrySpecification,
        grout_demand: SectionGroutDemand,
        options: CompressionDesignOptions | None = None,
    ) -> CompressionVerificationResult:
        """Verifica a conformidade normativa de uma seção com perfil de grauteamento pré-definido.

        Args:
            section: Seção resistente analisada.
            forces: Esforços solicitantes atuantes.
            masonry_spec: Especificação de alvenaria.
            grout_demand: Perfil de grauteamento da seção resistente.
            options: Opções de verificação.

        Returns:
            CompressionVerificationResult detalhando aprovação de esbeltez, tensões e taxa de utilização.
        """
        opts = options or CompressionDesignOptions()

        t_ef = min(seg.thickness for seg in section.segments)
        slenderness = cls.calculate_slenderness(section.height, t_ef)
        r_factor = cls.calculate_reduction_factor(section.height, t_ef)
        slenderness_ok = (slenderness <= opts.max_slenderness) and (r_factor > 0.0)

        r_eff = r_factor if r_factor > 0.0 else 1.0
        eq_plane = cls.calculate_equivalent_stress_plane(
            forces=forces,
            properties=section.properties,
            r_factor=r_eff,
            k_flexure=opts.k_flexure,
        )

        stress_regime = MechanicsService.classify_stress_regime(forces)

        stress_ok = True
        max_ratio_seen = 0.0
        max_comp_stress = 0.0

        for seg in section.segments:
            seg_demand = grout_demand.find_segment_demand(seg.segment_id)
            if seg_demand is None:
                raise ValueError(
                    f"Demanda de grauteamento não encontrada para o segmento '{seg.segment_id}'."
                )

            p_start = seg.local_axis.start
            p_end = seg.local_axis.end
            l_seg = seg.effective_length

            for inv in seg_demand.intervals:
                t_a = inv.start_offset / l_seg
                t_b = inv.end_offset / l_seg
                pt_a_x = p_start.x + t_a * (p_end.x - p_start.x)
                pt_a_y = p_start.y + t_a * (p_end.y - p_start.y)
                pt_b_x = p_start.x + t_b * (p_end.x - p_start.x)
                pt_b_y = p_start.y + t_b * (p_end.y - p_start.y)

                sig_a = eq_plane.stress_at(pt_a_x, pt_a_y)
                sig_b = eq_plane.stress_at(pt_b_x, pt_b_y)

                comp_peak = max(-sig_a, -sig_b, 0.0)
                if comp_peak > max_comp_stress:
                    max_comp_stress = comp_peak

                fd_inv = masonry_spec.calculate_fd(gamma_m=opts.gamma_m, grout_ratio=inv.ratio)
                if comp_peak > fd_inv + GEOMETRIC_TOLERANCE:
                    stress_ok = False

                if fd_inv > 0:
                    local_ratio = comp_peak / fd_inv
                    if local_ratio > max_ratio_seen:
                        max_ratio_seen = local_ratio

        fd_total_max = masonry_spec.fk_grouted / opts.gamma_m
        is_verified = slenderness_ok and stress_ok

        return CompressionVerificationResult(
            section=section,
            forces=forces,
            masonry_spec=masonry_spec,
            grout_demand=grout_demand,
            options=opts,
            slenderness=slenderness,
            slenderness_reduction_factor=r_factor,
            max_equivalent_compressive_stress=max_comp_stress,
            allowable_stress=fd_total_max,
            utilization_ratio=max_ratio_seen,
            is_verified=is_verified,
            slenderness_ok=slenderness_ok,
            stress_ok=stress_ok,
            stress_regime=stress_regime,
        )
