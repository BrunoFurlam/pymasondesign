from __future__ import annotations

from attrs import define, field
from pymasondesign.common import to_tuple
from pymasondesign.structure.floor_plan_model import FloorPlanModel
from pymasondesign.structure.story_model import StoryModel


@define(frozen=True, slots=True)
class BuildingModel:
    """Modelo estrutural da edificação completa contendo o catálogo de plantas e pavimentos ordenados de cima para baixo.

    Attributes:
        building_id: Identificador do edifício ou projeto (ex.: "EDIFICIO_AURORA").
        floor_plan_models: Catálogo imutável dos modelos de planta baixa utilizados no edifício.
        stories: Coleção imutável de StoryModel ordenada estritamente de cima para baixo (Z decrescente).
    """

    building_id: str = field(converter=str)
    floor_plan_models: tuple[FloorPlanModel, ...] = field(default=(), converter=to_tuple)
    stories: tuple[StoryModel, ...] = field(default=(), converter=to_tuple)

    def __attrs_post_init__(self) -> None:
        if not self.stories:
            raise ValueError(f"O modelo da edificação '{self.building_id}' deve conter ao menos 1 pavimento (stories).")

        if not self.floor_plan_models:
            raise ValueError(
                f"O modelo da edificação '{self.building_id}' deve conter ao menos 1 modelo de planta baixa no catálogo."
            )

        # 1. Unicidade de story_id
        seen_story_ids: set[str] = set()
        for st in self.stories:
            if st.story_id in seen_story_ids:
                raise ValueError(f"ID de pavimento duplicado na edificação '{self.building_id}': '{st.story_id}'.")
            seen_story_ids.add(st.story_id)

        # 2. Unicidade de plan_id no catálogo
        seen_plan_ids: set[str] = set()
        for fpm in self.floor_plan_models:
            if fpm.plan_id in seen_plan_ids:
                raise ValueError(
                    f"ID de planta duplicado no catálogo da edificação '{self.building_id}': '{fpm.plan_id}'."
                )
            seen_plan_ids.add(fpm.plan_id)

        # 3. Integridade referencial: todo story.plan_id deve existir no catálogo
        for st in self.stories:
            if st.plan_id not in seen_plan_ids:
                raise ValueError(
                    f"O pavimento '{st.story_id}' referencia a planta '{st.plan_id}', "
                    f"que não consta no catálogo de plantas da edificação '{self.building_id}'."
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
        """Número total de pavimentos na edificação."""
        return len(self.stories)

    @property
    def top_story(self) -> StoryModel:
        """Pavimento mais alto (topo) da edificação."""
        return self.stories[0]

    @property
    def bottom_story(self) -> StoryModel:
        """Pavimento mais baixo (base/térreo) da edificação."""
        return self.stories[-1]

    @property
    def total_height(self) -> float:
        """Altura total da edificação, do piso do nível inferior até o topo do nível superior."""
        top = self.top_story
        bot = self.bottom_story
        return (top.elevation + top.story_height) - bot.elevation

    def get_floor_plan_model(self, plan_id: str) -> FloorPlanModel | None:
        """Busca um modelo de planta baixa no catálogo pelo seu identificador."""
        for fpm in self.floor_plan_models:
            if fpm.plan_id == plan_id:
                return fpm
        return None

    def find_story(self, story_id: str) -> StoryModel | None:
        """Busca um pavimento na edificação pelo seu identificador."""
        for st in self.stories:
            if st.story_id == story_id:
                return st
        return None

    def find_stories_by_plan(self, plan_id: str) -> tuple[StoryModel, ...]:
        """Retorna todos os pavimentos da edificação que utilizam a planta baixa indicada."""
        return tuple(st for st in self.stories if st.plan_id == plan_id)

    def get_story_plan_model(self, story_or_id: StoryModel | str) -> FloorPlanModel:
        """Obtém o modelo de planta baixa (FloorPlanModel) associado ao pavimento informado.

        Args:
            story_or_id: Instância de StoryModel ou string com o story_id.

        Raises:
            KeyError: Caso o pavimento ou o modelo de planta correspondente não sejam encontrados.
        """
        if isinstance(story_or_id, StoryModel):
            story = story_or_id
        else:
            story = self.find_story(story_or_id)
            if story is None:
                raise KeyError(f"Pavimento '{story_or_id}' não encontrado na edificação '{self.building_id}'.")

        fpm = self.get_floor_plan_model(story.plan_id)
        if fpm is None:
            raise KeyError(f"Planta '{story.plan_id}' não encontrada no catálogo da edificação '{self.building_id}'.")
        return fpm
