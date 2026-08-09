from __future__ import annotations

from attrs import define, field
from pymasondesign.drafting.floor_plan import FloorPlan
from pymasondesign.drafting.story import Story


def _convert_plans(
    val: tuple[FloorPlan, ...] | list[FloorPlan] | None,
) -> tuple[FloorPlan, ...]:
    if val is None:
        return ()
    return tuple(val)


def _convert_stories(
    val: tuple[Story, ...] | list[Story] | None,
) -> tuple[Story, ...]:
    if val is None:
        return ()
    return tuple(val)


@define(frozen=True, slots=True)
class Building:
    """Representação do edifício completo no lançamento físico (drafting).

    Agrega o catálogo de plantas baixas (FloorPlan) e os pavimentos (Story) organizados
    em ordem estrita de cima para baixo (cota Z decrescente).

    Attributes:
        building_id: Identificador único do edifício ou projeto (ex.: "EDIFICIO_AURORA").
        floor_plans: Catálogo imutável de plantas baixas utilizadas no edifício.
        stories: Coleção imutável de pavimentos ordenada de cima para baixo (Z decrescente).
    """

    building_id: str = field(converter=str)
    floor_plans: tuple[FloorPlan, ...] = field(default=(), converter=_convert_plans)
    stories: tuple[Story, ...] = field(default=(), converter=_convert_stories)

    def __attrs_post_init__(self) -> None:
        # 1. Unicidade de story_id
        seen_story_ids: set[str] = set()
        for st in self.stories:
            if st.story_id in seen_story_ids:
                raise ValueError(f"ID de pavimento duplicado no edifício '{self.building_id}': '{st.story_id}'.")
            seen_story_ids.add(st.story_id)

        # 2. Unicidade de plan_id no catálogo de plantas
        seen_plan_ids: set[str] = set()
        for fp in self.floor_plans:
            if fp.plan_id in seen_plan_ids:
                raise ValueError(
                    f"ID de planta duplicado no catálogo do edifício '{self.building_id}': '{fp.plan_id}'."
                )
            seen_plan_ids.add(fp.plan_id)

        # 3. Integridade referencial: todo story.plan_id deve existir no catálogo de floor_plans
        for st in self.stories:
            if st.plan_id not in seen_plan_ids:
                raise ValueError(
                    f"O pavimento '{st.story_id}' referencia a planta '{st.plan_id}', "
                    f"que não consta no catálogo de plantas do edifício '{self.building_id}'."
                )

        # 4. Ordenação estrita de cima para baixo (Z decrescente)
        for i in range(len(self.stories) - 1):
            upper = self.stories[i]
            lower = self.stories[i + 1]
            if upper.elevation <= lower.elevation:
                raise ValueError(
                    f"Os pavimentos devem estar ordenados estritamente de cima para baixo (cota Z decrescente). "
                    f"O pavimento '{upper.story_id}' (cota {upper.elevation}) não é estritamente superior a "
                    f"'{lower.story_id}' (cota {lower.elevation})."
                )

    @property
    def num_stories(self) -> int:
        """Número total de pavimentos no edifício."""
        return len(self.stories)

    @property
    def top_story(self) -> Story | None:
        """Pavimento mais alto (topo) do edifício, ou None se não houver pavimentos."""
        return self.stories[0] if self.stories else None

    @property
    def bottom_story(self) -> Story | None:
        """Pavimento mais baixo (base/térreo) do edifício, ou None se não houver pavimentos."""
        return self.stories[-1] if self.stories else None

    @property
    def total_height(self) -> float:
        """Altura total da edificação (cota de topo do nível superior menos cota do piso do nível inferior)."""
        if not self.stories:
            return 0.0
        top = self.stories[0]
        bot = self.stories[-1]
        return (top.elevation + top.story_height) - bot.elevation

    def get_floor_plan(self, plan_id: str) -> FloorPlan | None:
        """Busca uma planta baixa no catálogo pelo seu identificador."""
        for fp in self.floor_plans:
            if fp.plan_id == plan_id:
                return fp
        return None

    def find_story(self, story_id: str) -> Story | None:
        """Busca um pavimento no edifício pelo seu identificador."""
        for st in self.stories:
            if st.story_id == story_id:
                return st
        return None

    def find_stories_by_plan(self, plan_id: str) -> tuple[Story, ...]:
        """Retorna todos os pavimentos do edifício que utilizam a planta baixa indicada."""
        return tuple(st for st in self.stories if st.plan_id == plan_id)

    def get_story_floor_plan(self, story_or_id: Story | str) -> FloorPlan:
        """Obtém a planta baixa (FloorPlan) associada ao pavimento informado.

        Args:
            story_or_id: Instância de Story ou string com o story_id.

        Raises:
            KeyError: Caso o pavimento ou a planta correspondente não sejam encontrados.
        """
        if isinstance(story_or_id, Story):
            story = story_or_id
        else:
            story = self.find_story(story_or_id)
            if story is None:
                raise KeyError(f"Pavimento '{story_or_id}' não encontrado no edifício '{self.building_id}'.")

        fp = self.get_floor_plan(story.plan_id)
        if fp is None:
            raise KeyError(f"Planta '{story.plan_id}' não encontrada no catálogo do edifício '{self.building_id}'.")
        return fp

    def add_floor_plan(self, floor_plan: FloorPlan) -> Building:
        """Retorna uma nova instância de Building incluindo a planta baixa informada no catálogo."""
        if self.get_floor_plan(floor_plan.plan_id) is not None:
            raise ValueError(f"Planta '{floor_plan.plan_id}' já existe no catálogo do edifício '{self.building_id}'.")
        return Building(
            building_id=self.building_id,
            floor_plans=(*self.floor_plans, floor_plan),
            stories=self.stories,
        )

    def add_story(self, story: Story) -> Building:
        """Retorna uma nova instância de Building incluindo o pavimento, mantendo a ordenação top-to-bottom."""
        if self.find_story(story.story_id) is not None:
            raise ValueError(f"Pavimento '{story.story_id}' já existe no edifício '{self.building_id}'.")
        new_stories = sorted((*self.stories, story), key=lambda s: s.elevation, reverse=True)
        return Building(
            building_id=self.building_id,
            floor_plans=self.floor_plans,
            stories=tuple(new_stories),
        )
