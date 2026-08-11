from __future__ import annotations

from attrs import field, frozen
from pymasondesign.common import to_tuple
from pymasondesign.geometry.tolerances import GEOMETRIC_TOLERANCE, is_close, is_zero
from pymasondesign.design.section import ResistantSection


@frozen
class GroutInterval:
    """Representa um trecho contínuo ao longo do segmento resistente com uma porcentagem de grauteamento requerida.

    Attributes:
        start_offset: Posição inicial no eixo local do segmento em cm ou m (s_start >= 0).
        end_offset: Posição final no eixo local do segmento (s_end > s_start).
        ratio: Fração/porcentagem de grauteamento requerida no intervalo (0.0 <= ratio <= 1.0).
    """

    start_offset: float = field(converter=float)
    end_offset: float = field(converter=float)
    ratio: float = field(converter=float)

    def __attrs_post_init__(self) -> None:
        if self.start_offset < 0.0:
            raise ValueError(
                f"start_offset do intervalo de grauteamento não pode ser negativo, obtido: {self.start_offset}."
            )
        if self.end_offset <= self.start_offset:
            raise ValueError(
                f"end_offset ({self.end_offset}) deve ser estritamente maior que start_offset ({self.start_offset})."
            )
        if self.ratio < 0.0 or self.ratio > 1.0:
            raise ValueError(
                f"Porcentagem de grauteamento (ratio) deve estar no intervalo [0.0, 1.0], obtido: {self.ratio}."
            )

    @property
    def length(self) -> float:
        """Comprimento do intervalo de grauteamento."""
        return self.end_offset - self.start_offset

    @property
    def is_fully_grouted(self) -> bool:
        """Indica se o intervalo é 100% grauteado (ratio == 1.0)."""
        return is_close(self.ratio, 1.0, GEOMETRIC_TOLERANCE)

    @property
    def is_ungrouted(self) -> bool:
        """Indica se o intervalo não possui grauteamento (ratio == 0.0)."""
        return is_zero(self.ratio, GEOMETRIC_TOLERANCE)

    def contains(self, offset: float, tolerance: float = GEOMETRIC_TOLERANCE) -> bool:
        """Verifica se uma cota escalar pertence a este intervalo dentro da tolerância."""
        return (self.start_offset - tolerance) <= offset <= (self.end_offset + tolerance)


@frozen
class SegmentGroutDemand:
    """Perfil consolidado de demanda de grauteamento ao longo de um ResistantSegment.

    Attributes:
        segment_id: Identificador do ResistantSegment associado.
        effective_length: Comprimento total do segmento resistente (L > 0).
        intervals: Coleção ordenada e contígua de GroutInterval cobrindo integralmente o trecho [0, L].
    """

    segment_id: str = field(converter=str)
    effective_length: float = field(converter=float)
    intervals: tuple[GroutInterval, ...] = field(converter=to_tuple)

    def __attrs_post_init__(self) -> None:
        if self.effective_length <= 0.0:
            raise ValueError(
                f"Comprimento efetivo do segmento deve ser positivo, obtido: {self.effective_length}."
            )
        if not self.intervals:
            raise ValueError(
                f"SegmentGroutDemand para o segmento '{self.segment_id}' deve conter ao menos um intervalo."
            )

        # Validação de ordenação e início em 0.0
        first = self.intervals[0]
        if not is_close(first.start_offset, 0.0, GEOMETRIC_TOLERANCE):
            raise ValueError(
                f"O primeiro intervalo de grauteamento deve iniciar em 0.0, obtido: {first.start_offset}."
            )

        # Validação de contiguidade entre intervalos consecutivos (sem sobreposições ou buracos)
        for i in range(len(self.intervals) - 1):
            curr_inv = self.intervals[i]
            next_inv = self.intervals[i + 1]
            if not is_close(curr_inv.end_offset, next_inv.start_offset, GEOMETRIC_TOLERANCE):
                raise ValueError(
                    f"Intervalos de grauteamento não contíguos no segmento '{self.segment_id}': "
                    f"intervalo {i} termina em {curr_inv.end_offset} e intervalo {i+1} inicia em {next_inv.start_offset}."
                )

        # Validação de término no comprimento efetivo
        last = self.intervals[-1]
        if not is_close(last.end_offset, self.effective_length, GEOMETRIC_TOLERANCE):
            raise ValueError(
                f"O último intervalo de grauteamento deve terminar em effective_length ({self.effective_length}), "
                f"obtido: {last.end_offset}."
            )

    @classmethod
    def uniform(
        cls,
        segment_id: str,
        effective_length: float,
        ratio: float = 1.0,
    ) -> SegmentGroutDemand:
        """Cria uma demanda uniforme de grauteamento ao longo de todo o segmento resistente."""
        inv = GroutInterval(start_offset=0.0, end_offset=effective_length, ratio=ratio)
        return cls(
            segment_id=segment_id,
            effective_length=effective_length,
            intervals=(inv,),
        )

    @classmethod
    def from_spans(
        cls,
        segment_id: str,
        effective_length: float,
        spans: list[tuple[float, float, float]] | tuple[tuple[float, float, float], ...],
    ) -> SegmentGroutDemand:
        """Cria uma demanda a partir de uma tupla/lista de trechos (start, end, ratio).

        Args:
            segment_id: Identificador do segmento.
            effective_length: Comprimento total do segmento.
            spans: Sequência de tuplas (start_offset, end_offset, ratio).
        """
        intervals = tuple(
            GroutInterval(start_offset=s, end_offset=e, ratio=r) for s, e, r in spans
        )
        return cls(
            segment_id=segment_id,
            effective_length=effective_length,
            intervals=intervals,
        )

    @property
    def average_ratio(self) -> float:
        """Média ponderada da porcentagem de grauteamento pelo comprimento dos trechos."""
        weighted_sum = sum(inv.length * inv.ratio for inv in self.intervals)
        return weighted_sum / self.effective_length

    @property
    def max_ratio(self) -> float:
        """Porcentagem máxima de graute demandada no segmento."""
        return max(inv.ratio for inv in self.intervals)

    @property
    def min_ratio(self) -> float:
        """Porcentagem mínima de graute demandada no segmento."""
        return min(inv.ratio for inv in self.intervals)

    @property
    def is_fully_grouted(self) -> bool:
        """Indica se 100% do comprimento do segmento exige grauteamento total."""
        return all(inv.is_fully_grouted for inv in self.intervals)

    @property
    def is_ungrouted(self) -> bool:
        """Indica se 0% do comprimento do segmento exige grauteamento."""
        return all(inv.is_ungrouted for inv in self.intervals)

    def find_interval(
        self, offset: float, tolerance: float = GEOMETRIC_TOLERANCE
    ) -> GroutInterval | None:
        """Busca o GroutInterval que contém a cota escalar informada."""
        for inv in self.intervals:
            if inv.contains(offset, tolerance=tolerance):
                return inv
        return None

    def ratio_at(self, offset: float, tolerance: float = GEOMETRIC_TOLERANCE) -> float:
        """Retorna a porcentagem de grauteamento exigida em uma cota específica ao longo do segmento.

        Args:
            offset: Cota escalar a partir do início do segmento (0 <= offset <= effective_length).
            tolerance: Tolerância para os limites de borda.

        Returns:
            Porcentagem/razão de grauteamento demandada no ponto.
        """
        inv = self.find_interval(offset, tolerance=tolerance)
        if inv is None:
            raise ValueError(
                f"Cota {offset} fora do domínio [0.0, {self.effective_length}] do segmento '{self.segment_id}'."
            )
        return inv.ratio


@frozen
class SectionGroutDemand:
    """Demanda consolidada de grauteamento para todos os segmentos de uma ResistantSection.

    Attributes:
        section_id: Identificador da ResistantSection associada.
        segment_demands: Coleção de SegmentGroutDemand de cada segmento da seção.
    """

    section_id: str = field(converter=str)
    segment_demands: tuple[SegmentGroutDemand, ...] = field(converter=to_tuple)

    def __attrs_post_init__(self) -> None:
        if not self.segment_demands:
            raise ValueError(
                f"SectionGroutDemand para a seção '{self.section_id}' deve conter ao menos uma demanda de segmento."
            )

        seen_ids = set()
        for sd in self.segment_demands:
            if sd.segment_id in seen_ids:
                raise ValueError(
                    f"Demanda de segmento duplicada na seção '{self.section_id}': '{sd.segment_id}'."
                )
            seen_ids.add(sd.segment_id)

    @classmethod
    def uniform(
        cls,
        section: ResistantSection,
        ratio: float = 1.0,
    ) -> SectionGroutDemand:
        """Cria uma demanda de grauteamento uniforme para todos os segmentos da seção resistente."""
        demands = tuple(
            SegmentGroutDemand.uniform(
                segment_id=seg.segment_id,
                effective_length=seg.effective_length,
                ratio=ratio,
            )
            for seg in section.segments
        )
        return cls(
            section_id=section.section_id,
            segment_demands=demands,
        )

    @property
    def total_length(self) -> float:
        """Soma dos comprimentos efetivos de todos os segmentos da seção."""
        return sum(sd.effective_length for sd in self.segment_demands)

    @property
    def weighted_average_ratio(self) -> float:
        """Média ponderada da porcentagem de grauteamento de toda a seção."""
        total_l = self.total_length
        if total_l <= 0.0:
            return 0.0
        return (
            sum(sd.average_ratio * sd.effective_length for sd in self.segment_demands)
            / total_l
        )

    @property
    def is_fully_grouted(self) -> bool:
        """Indica se todos os segmentos da seção exigem grauteamento total (100%)."""
        return all(sd.is_fully_grouted for sd in self.segment_demands)

    @property
    def is_ungrouted(self) -> bool:
        """Indica se toda a seção é não-grauteada (0%)."""
        return all(sd.is_ungrouted for sd in self.segment_demands)

    def find_segment_demand(self, segment_id: str) -> SegmentGroutDemand | None:
        """Busca a demanda de grauteamento de um segmento específico pelo identificador."""
        for sd in self.segment_demands:
            if sd.segment_id == segment_id:
                return sd
        return None
