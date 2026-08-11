# PyMasonDesign — Arquitetura Técnica do Sistema

Este documento descreve a arquitetura de software, princípios de projeto, organização modular, modelos de domínio e decisões de engenharia do **PyMasonDesign**.

---

## 1. Visão Geral da Arquitetura

O **PyMasonDesign** foi projetado seguindo os princípios de **Domain-Driven Design (DDD)**, **Programação Funcional Imutável** e **Arquitetura em Camadas Desacopladas**. O núcleo não possui dependências de frameworks de interface gráfica, banco de dados ou engines CAD/BIM externos, garantindo máxima portabilidade, determinismo e facilidade de testes unitários.

```mermaid
graph TD
    subgraph "Camada de Aplicação / Consumidores"
        A[Revit / CAD Plugins]
        B[CLI Tools]
        C[Web / Cloud Engines]
    end

    subgraph "pymasondesign (Core)"
        subgraph "Dimensionamento e Seções Resistentes (Design)"
            DESIGN[design<br/>ResistantSection, ResistantSegment, FlangeOptions, ResistantSectionService]
        end

        subgraph "Modelo Estrutural Analítico (Structure)"
            STRUCT[structure<br/>BuildingModel, StoryModel, FloorPlanModel, MasonryPanel, PanelGroup]
        end

        subgraph "Lançamento e Topologia (Drafting)"
            DRAFT[drafting<br/>Building, Story, FloorPlan, Wall, Opening, Junction]
        end

        subgraph "Mecânica e Análise Seccional (Mechanics)"
            MECH[mechanics<br/>MechanicsService, NormalStressPlane, SectionForces]
        end

        subgraph "Seções e Inércias (Sections)"
            SECT[sections<br/>Section, RectangularSection, PolygonSection, CompositeSection]
        end

        subgraph "Materiais e NBR 16868 (Materials)"
            MAT[materials<br/>MasonrySpecification, NBR16868MasonryFactory, Steel, Block]
        end

        subgraph "Fundação Geométrica Pura (Geometry)"
            GEOM[geometry<br/>Point2D, Vector2D, Axis, Polygon, Transform2D, Tolerances]
        end
    end

    A --> DRAFT
    B --> DRAFT
    C --> DRAFT
    DRAFT --> GEOM
    DRAFT --> MAT
    STRUCT --> DRAFT
    STRUCT --> GEOM
    DESIGN --> STRUCT
    DESIGN --> SECT
    DESIGN --> GEOM
    MECH --> SECT
    MECH --> GEOM
    SECT --> GEOM
    MAT --> GEOM
```

---

## 2. Princípios Arquiteturais e Diretrizes de Design

### 2.1. Imutabilidade e Thread-Safety com `attrs`
- Todas as estruturas de dados fundamentais (`Point2D`, `Axis`, `Wall`, `FloorPlan`, `NormalStressPlane`, etc.) são decoradas com `@define` ou `@frozen` da biblioteca `attrs`.
- Instâncias são **imutáveis**. Qualquer operação de modificação retorna uma nova instância do objeto através de métodos alinhados à intenção de domínio (ex.: `floor_plan.add_wall(...)`, `floor_plan.add_opening(...)`, `axis.translated(...)`, `axis.reversed(...)`), sem mutações in-place e sem métodos genéricos `with_...`.
- Benefícios: thread-safety nativo, eliminação de efeitos colaterais (side-effects), histórico de alterações determinístico e performance otimizada com `__slots__`.

### 2.2. Tolerâncias Numéricas Centralizadas
- Cálculos geométricos e comparações de ponto flutuante utilizam o módulo centralizado `pymasondesign.geometry.tolerances`.
- É **proibido** utilizar comparações diretas de igualdade (`a == b`) para coordenadas e floats. Sempre utilizar `is_close()`, `is_zero()`, `is_within_unit()`, etc.
- Constantes padronizadas:
  - `GEOMETRIC_TOLERANCE = 1e-9`: Comparações geométricas de alta precisão.
  - `JUNCTION_TOLERANCE = 1e-4`: Detecção de encontros topológicos de paredes.
  - `OVERLAP_TOLERANCE = 1e-9`: Validação de sobreposição de vãos e aberturas.
  - `DIVISION_GUARD = 1e-15`: Proteção contra singularidades numéricas.

### 2.3. Resolução Analítica Exata
- Propriedades de seções poligonais são calculadas via fórmulas de integração de contorno (Teorema de Green / Shoelace), evitando aproximações de malha (mesh) desnecessárias.
- A integração de tensões normais lineares utiliza o **Teorema da Média**:
  $$\int_A \sigma(x, y)\, dA = A \cdot \sigma(x_{cg}, y_{cg})$$
  onde $(x_{cg}, y_{cg})$ é o centróide da seção.

---

## 3. Módulos do Sistema

### 3.1. `pymasondesign.geometry` (Geometria 2D e Tolerâncias)
Fornece primitivas vetoriais e matriciais 2D puras:
- **`Point2D`**: Coordenadas cartesianas $(x, y)$, cálculo de distâncias euclidianas, equivalência com tolerância (`is_same(other, tolerance)`) e translações.
- **`Vector2D`**: Operações vetoriais (soma, subtração, produto escalar, produto vetorial 2D `cross`, rotação $90^\circ$, normalização e projeção).
- **`Axis`**: Eixo orientado no plano definido por `start` e `end`. Provê vetor diretor unitário, vetor normal, comprimento, ponto intermediário via parâmetro $t \in [0, 1]$, projeção ortogonal escalar (`projected_offset(point)`), menor distância a ponto (`distance_to_point(point)`) e detecção analítica de interseções (`intersect()`).
- **`AxisRelation` & `AxisIntersectionResult`**: Classificação de relações entre eixos (`POINT_INTERSECT`, `TOUCHING_VERTEX`, `OVERLAPPING`, `PARALLEL`, `COLINEAR`, `DISJOINT`).
- **`Transform2D`**: Transformações afins 2D representadas por matrizes homogêneas $3 \times 3$ (translação, rotação em radianos ou graus, escala).
- **`Polygon`**: Polígono 2D simples ou complexo, cálculo de área com sinal, centróide, inversão de sentido dos vértices e teste de ponto interno via *ray-casting*.
- **`BoundingBox`**: Retângulo envolvente alinhado aos eixos $(x_{\min}, x_{\max}, y_{\min}, y_{\max})$.

---

### 3.2. `pymasondesign.sections` (Seções Transversais e Inércias)
Abstração para cálculo de propriedades geométricas de seções transversais estruturais:
- **`Section`** (Classe Base Abstrata): Define o contrato `compute_properties() -> SectionProperties`.
- **`SectionProperties`**: Encapsula as propriedades calculadas da seção:
  - Área bruta ($A$).
  - Centro de Gravidade ($C_G = (x_{cg}, y_{cg})$).
  - Momentos de Inércia centrais ($I_{xx}, I_{yy}$).
  - Produto de Inércia central ($I_{xy}$).
  - Momentos Principais de Inércia ($I_u, I_v$) e ângulo de rotação principal ($\theta_p$).
  - Raios de Giração ($r_x, r_y$).
  - Módulos de Resistência Elástica ($W_x, W_y$).
- **`RectangularSection`**: Seção retangular homogênea $(b, h)$.
- **`PolygonSection`**: Seção poligonal arbitrária com cálculo analítico de $I_{xx}, I_{yy}, I_{xy}$ em relação ao centróide.
- **`CompositeSection` & `SectionComponent`**: Seção composta por múltiplos componentes (polígonos ou retângulos) com posições relativas e coeficientes de ponderação/homogeneização modular ($n = E_i / E_0$).

---

### 3.3. `pymasondesign.mechanics` (Mecânica das Estruturas e Tensões)
Implementação de modelos seccionais e análise de tensões normais:
- **`SectionForces`**: Vetor de esforços internos solicitantes seccionais ($N, M_x, M_y, V_x, V_y, T$).
- **`NormalStressPlane`**: Equação do plano linear de tensões normais:
  $$\sigma(x, y) = c_0 + c_x \cdot x + c_y \cdot y$$
- **`StressRegime`**: Classificação do estado de tensões na seção:
  - `FULL_COMPRESSION` (Totalmente comprimida: $\sigma \le 0$).
  - `PARTIAL_COMPRESSION` (Flexo-compressão com tração parcial).
  - `FULL_TENSION` (Totalmente tracionada: $\sigma \ge 0$).
  - `ZERO_STRESS` (Tensão nula em toda a seção).
- **`MechanicsService`**:
  - `calculate_normal_stress_plane(forces, properties)`: Monta o plano de tensões a partir de $N, M_x, M_y$ e da matriz de inércia da seção (resolvendo a flexo-compressão biaxial oblíqua).
  - `calculate_eccentricities(forces)`: $e_x = |M_y / N|$ e $e_y = |M_x / N|$.
  - `calculate_extreme_stresses(plane, properties)`: Tensão mínima ($\sigma_{\min}$) e máxima ($\sigma_{\max}$).
  - `classify_stress_regime(plane, properties)`: Determina o regime de tensões atuante.
  - `integrate_normal_stress(plane, section)`: Integração analítica da força normal acumulada.

---

### 3.4. `pymasondesign.materials` (Materiais e Tabelas NBR 16868)
Especificações de materiais e compósitos de alvenaria:
- **`SteelSpecification`**: Aço para armaduras passivas (CA-50, CA-60), $f_{yk}$, módulo de elasticidade $E_s = 210\,000\text{ MPa}$, cálculo de $f_{yd} = f_{yk}/\gamma_s$ e deformação de escoamento $\epsilon_{yd}$.
- **`BlockSpecification`**: Blocos de concreto ou cerâmicos (paredes vazadas ou maciças) com resistência característica $f_{bk}$.
- **`MortarSpecification`**: Argamassa de assentamento com resistência média à compressão $f_a$.
- **`GroutSpecification`**: Graute com resistência característica à compressão $f_g$ ($f_{gk}$).
- **`MasonrySpecification`**: Especificação completa do compósito bloco + argamassa + graute, contendo $f_{pk}, f_{pgk}$, resistência característica da alvenaria $f_k$ e módulo de deformação longitudinal $E_{mod}$.
- **`NBR16868MasonryFactory`**: Fábrica que encapsula as tabelas normativas da ABNT NBR 16868:
  - `concrete_from_fbk(fbk)`: Tabela 1 para blocos de concreto ($f_{bk}$ de $3.0$ a $24.0\text{ MPa}$).
  - `ceramic_hollow_from_fbk(fbk)`: Tabela para blocos cerâmicos de paredes vazadas ($f_{bk}$ de $4.0$ a $12.0\text{ MPa}$).
  - `ceramic_solid_from_fbk(fbk)`: Tabela para blocos cerâmicos de paredes maciças ($f_{bk}$ de $7.0$ a $18.0\text{ MPa}$).

---

### 3.5. `pymasondesign.drafting` (Lançamento e Topologia Estrutural)
Modelagem arquitetural e estrutural de plantas e pavimentos:
- **`Opening`**: Vão na alvenaria (portas, janelas, passagens) com largura ($w$), altura ($h$), peitoril ($sill$), elevação e posição ao longo do eixo da parede (`offset_along_wall`).
- **`Wall`**: Parede estrutural imutável definida por seu identificador (`wall_id`), eixo geométrico 2D (`axis`), espessura nominal (`thickness`), altura (`height`), lista imutável de aberturas (`openings`) e tipos de amarração nas extremidades (`start_bond`, `end_bond`).
- **`PassingWall` & `ArrivingWall`**: Representação leve de paredes passantes e incidentes em nós de encontro, identificadas por `wall_id: str`.
- **`Junction`**: Nó estrutural de encontro de paredes (em L, T, X ou topo a topo), com localização topológica `point`, listas de paredes passantes e incidentes, e métodos de consulta (`has_wall`, `is_passing`, `is_arriving`, `get_participation`).
- **`FloorPlan`**: Planta baixa de alvenaria estrutural. Agrupa as paredes, calcula comprimento total, valida sobreposições de aberturas, detecta nós de encontro (`find_junctions()`), calcula zonas de exclusão e valida amarrações.
- **`Story`**: Pavimento estrutural físico no lançamento, associando elevação $Z$, altura piso a piso, especificação de material (`MasonrySpecification`) e referência desacoplada à planta via `plan_id: str`.
- **`Building`**: Edifício completo no lançamento físico (drafting). Agrega o catálogo de plantas baixas (`floor_plans`) e a coleção de pavimentos (`stories`) mantida e validada em ordem estrita de cima para baixo ($Z$ decrescente). Provê consultas de catálogo, busca de níveis e métodos de mutação funcional (`add_floor_plan`, `add_story`).

---

### 3.6. `pymasondesign.structure` (Modelos e Serviços de Estrutura Analítica)
Camada de transição entre a topologia física (*drafting*) e o modelo de dimensionamento analítico:
- **`MasonryPanel` (Piers / Painéis Resistentes)**: Segmentos resistentes de parede contínuos delimitados por extremidades de parede, vãos de abertura ou nós de encontro (`panel_id`, `wall_id`, `axis`, `thickness`, `height`, `length`).
- **`PanelGroup` (Grupos Conexos de Painéis)**: Subconjunto de painéis conectados solidariamente por amarração direta (`BondType.DIRECT`) ou continuidade de parede passante (`group_id`, `panels`, `total_length`, `wall_ids`, `find_panel`).
- **`FloorPlanModel` (Modelo Estrutural da Planta/Pavimento)**: Modelo estrutural que agrega todos os `PanelGroup` derivados de um `FloorPlan`, permitindo a reutilização em múltiplos pavimentos tipo (`plan_id`, `height`, `groups`, `panels`, `total_length`, `wall_ids`, `find_group`, `find_panel`, `find_groups_by_wall`).
- **`StoryModel` (Modelo Estrutural do Pavimento)**: Modelo estrutural de um nível no edifício, associando cota $Z$, altura piso a piso, especificação de alvenaria e referência por ID (`plan_id`) ao modelo de planta adotado.
- **`BuildingModel` (Modelo Estrutural da Edificação Completa)**: Modelo global que agrega o catálogo de plantas (`floor_plan_models`) e a coleção de pavimentos (`stories: tuple[StoryModel, ...]`) mantida e validada estritamente **de cima para baixo** (cota $Z$ decrescente) para suporte à acumulação de cargas e dimensionamento estrutural.
- **`MasonryPanelService`**: Serviço de domínio responsável pela discretização de paredes em painéis (`derive_panels_from_wall`), extração de componentes conexas (`group_panels_by_direct_bond`), derivação do modelo de planta (`derive_floor_plan_model`) e derivação da edificação completa (`derive_building_model`).

---

### 3.7. `pymasondesign.design` (Dimensionamento e Seções Resistentes)
Modelagem das seções transversais resistentes estruturais com almas e abas colaborantes:
- **`SegmentRole`**: Classificação funcional do segmento na seção (`WEB` para alma principal e `FLANGE` para aba colaborante transversal).
- **`FlangeOptions`**: Configuração das regras de largura colaborante de aba ($b_f$), incluindo multiplicador sobre a espessura da alma ($k \cdot t_{web}$, padrão 6.0 da NBR 16868-1) e largura customizada fixa.
- **`ResistantSegment`**: Segmento de alma ou aba componente da seção contendo identificação, papel funcional, eixos e polígonos retangulares exatos tanto no sistema local quanto global, espessura, comprimento efetivo e altura livre (`height`).
- **`GroutInterval`**: Trecho contínuo ao longo do segmento resistente com porcentagem/fração de graute demandada ($0.0 \le \text{ratio} \le 1.0$).
- **`SegmentGroutDemand`**: Perfil consolidado e contíguo de demanda de grauteamento ao longo de um `ResistantSegment`, com cálculo de média ponderada, consultas pontuais por cota (`ratio_at(offset)`) e identificação de estado (`is_fully_grouted`, `is_ungrouted`).
- **`SectionGroutDemand`**: Demanda consolidada de grauteamento para todos os segmentos de uma `ResistantSection` (almas e abas), servindo de resultado do dimensionamento para posterior discretização modular.
- **`ResistantSectionService`**: Serviço de domínio para derivação de seções resistentes:
  - `derive_for_group(group, direction, options)`: Identifica almas, agrupa almas acopladas por painel transversal somente quando $L_{transversal} < k\cdot t_1 + k\cdot t_2$ (desacoplando em seções distintas caso contrário), calcula projeção de abas para fora das faces externas da alma (precedência da alma), particiona vãos entre almas paralelas ($s/2$), monta o sistema local de coordenadas e calcula as propriedades seccionais.
  - `derive_for_floor_plan(floor_plan_model, direction, options)`: Deriva todas as seções resistentes de todos os grupos de um pavimento para a direção analisada.

---

### 3.8. `pymasondesign.common` (Utilitários e Helpers Compartilhados)
Utilitários transversais e conversores genéricos:
- **`to_tuple`**: Conversor genérico tipado (`Iterable[T] | None -> tuple[T, ...]`), garantindo imutabilidade e simplificação de atributos `attrs` em todas as camadas da biblioteca.

---

## 4. Fluxo de Dados Típico

```mermaid
sequenceDiagram
    participant User as Engenheiro / Plugin BIM
    participant Drafting as Drafting (FloorPlan / Wall)
    participant Struct as Structure (MasonryPanelService)
    participant Sect as Sections (SectionProperties)
    participant Mech as Mechanics & Design (MechanicsService)

    User->>Drafting: Cria paredes e aberturas na FloorPlan
    Drafting-->>Drafting: Valida topologia e detecta Junctions
    Drafting->>Struct: Discretiza paredes em MasonryPanels e PanelGroups
    Struct-->>Struct: Agrupa painéis por amarração direta
    Struct->>Sect: Gera seções transversais (simples e compostas)
    Sect-->>Struct: Propriedades seccionais (A, CG, Ixx, Iyy, W)
    User->>Mech: Aplica carregamentos / ações nos elementos
    Mech->>Mech: Calcula planos de tensão, flexo-compressão e esbeltez
    Mech-->>User: Verificações normativas ELU/ELS
```

---

## 5. Padrões de Código e Convenções

1. **Tipagem Estrita**: Todos os métodos e funções devem possuir assinaturas com type hints completos e `from __future__ import annotations`.
2. **Imutabilidade**: Nenhum atributo deve ser modificado in-place. Classes do domínio devem usar `attrs` com `frozen=True, slots=True`.
3. **Validação Eager**: Validações de domínio são disparadas no `__attrs_post_init__` ou nos métodos de fábrica (ex.: espessura $> 0$, comprimento $> 0$, aberturas dentro do comprimento da parede).
4. **Sem Efeitos Colaterais**: Funções devem ser puras sempre que possível, facilitando o reuso em cálculos paralelos e pipelines assíncronos.
