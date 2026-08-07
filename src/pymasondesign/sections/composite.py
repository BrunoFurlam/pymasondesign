from __future__ import annotations

from attrs import define, field, Factory
from pymasondesign.geometry.point import Point2D
from pymasondesign.geometry.bounds import BoundingBox
from pymasondesign.sections.base import Section
from pymasondesign.sections.properties import SectionProperties


@define(frozen=True, slots=True)
class SectionComponent:
    """Componente individual de uma seção composta.

    Attributes:
        section: A seção geométrica (retângulo, polígono, etc.).
        is_void: Se True, a seção é tratada como vazio/furo (área subtraída).
    """

    section: Section
    is_void: bool = False


@define(slots=True)
class CompositeSection(Section):
    """Seção composta por múltiplas sub-seções sólidas e vazios/furos.

    Aplica o Teorema dos Eixos Paralelos (Teorema de Steiner) para calcular
    a área líquida, o centro de gravidade combinado e os momentos de inércia.
    """

    components: list[SectionComponent] = field(default=Factory(list))

    def add_section(self, section: Section, is_void: bool = False) -> CompositeSection:
        """Adiciona uma sub-seção (sólida ou furo) e retorna a própria instância para encadeamento."""
        self.components.append(SectionComponent(section=section, is_void=is_void))
        return self

    def add_solid(self, section: Section) -> CompositeSection:
        """Adiciona uma sub-seção sólida."""
        return self.add_section(section, is_void=False)

    def add_void(self, section: Section) -> CompositeSection:
        """Adiciona um furo/vazio a ser subtraído da seção."""
        return self.add_section(section, is_void=True)

    def compute_properties(self) -> SectionProperties:
        if not self.components:
            raise ValueError("CompositeSection não possui componentes adicionados.")

        total_area = 0.0
        qx = 0.0
        qy = 0.0

        comp_props: list[tuple[SectionProperties, float]] = []

        all_xmin: list[float] = []
        all_xmax: list[float] = []
        all_ymin: list[float] = []
        all_ymax: list[float] = []

        for comp in self.components:
            props = comp.section.compute_properties()
            sign = -1.0 if comp.is_void else 1.0

            total_area += sign * props.area
            qx += sign * props.area * props.cg.y
            qy += sign * props.area * props.cg.x
            comp_props.append((props, sign))

            if not comp.is_void:
                all_xmin.append(props.bounds.xmin)
                all_xmax.append(props.bounds.xmax)
                all_ymin.append(props.bounds.ymin)
                all_ymax.append(props.bounds.ymax)

        if total_area <= 0:
            raise ValueError(f"Área líquida resultante deve ser positiva, obtido: {total_area}.")

        x_cg = qy / total_area
        y_cg = qx / total_area
        cg = Point2D(x_cg, y_cg)

        # Teorema de Steiner (Eixos Paralelos) em relação a (x_cg, y_cg)
        ixx = 0.0
        iyy = 0.0
        ixy = 0.0

        for props, sign in comp_props:
            dx = props.cg.x - x_cg
            dy = props.cg.y - y_cg

            ixx += sign * (props.ixx + props.area * (dy**2))
            iyy += sign * (props.iyy + props.area * (dx**2))
            ixy += sign * (props.ixy + props.area * dx * dy)

        bounds = BoundingBox(
            xmin=min(all_xmin) if all_xmin else 0.0,
            xmax=max(all_xmax) if all_xmax else 0.0,
            ymin=min(all_ymin) if all_ymin else 0.0,
            ymax=max(all_ymax) if all_ymax else 0.0,
        )

        return SectionProperties(
            area=total_area,
            ixx=ixx,
            iyy=iyy,
            ixy=ixy,
            cg=cg,
            bounds=bounds,
        )
