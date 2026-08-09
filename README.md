# PyMasonDesign

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![ABNT NBR 16868](https://img.shields.io/badge/Standard-ABNT%20NBR%2016868-green.svg)](https://www.abnt.org.br/)

**PyMasonDesign** é um núcleo computacional (*core engine*) em Python puro para modelagem geométrica, análise de tensões, dimensionamento e verificação de estruturas em **Alvenaria Estrutural**, em conformidade com as normas brasileiras (**ABNT NBR 16868:2020**).

Projetado com base em imutabilidade estrita (`attrs`), alta precisão numérica e desacoplamento total de bibliotecas gráficas, sendo ideal para aplicações *backend*, plugins BIM/CAD (ex: Autodesk Revit), ferramentas CLI e automações de cálculo estrutural.

---

## Documentação de Contexto e Arquitetura

- 📘 [**Contexto do Projeto e Domínio de Engenharia (PROJECT_CONTEXT.md)**](PROJECT_CONTEXT.md): Visão do produto, objetivos, normas ABNT NBR 16868, roadmap e glossário técnico.
- 📐 [**Arquitetura Técnica do Sistema (ARCHITECTURE.md)**](ARCHITECTURE.md): Diagramas de arquitetura, princípios de design, modelos de domínio e detalhes dos módulos.
- 🤖 [**Diretrizes para Agentes de IA e Desenvolvedores (.agents/AGENTS.md)**](.agents/AGENTS.md): Convenções de código, padrões de imutabilidade e regras de teste.

---

## Estrutura dos Módulos

```text
pymasondesign
├── geometry/       # Primitivas vetoriais 2D, eixos, transformações afins 3x3 e tolerâncias
├── sections/       # Seções transversais (retangulares, poligonais, compostas) e inércias
├── mechanics/      # Flexo-compressão oblíqua, planos de tensão e regimes seccionais
├── materials/      # Blocos, argamassa, graute, aço e tabelas normativas NBR 16868
└── drafting/       # Pavimentos, plantas baixas, paredes, vãos e encontros topológicos
```

---

## Exemplos Rápidos de Uso

### 1. Criando uma Planta Baixa com Paredes e Aberturas (`drafting`)

```python
from pymasondesign.geometry import Point2D, Axis
from pymasondesign.drafting import FloorPlan, Wall, Opening, OpeningType, BondType

# Definição dos eixos das paredes (dimensões em metros)
axis_p1 = Axis(start=Point2D(0.0, 0.0), end=Point2D(5.0, 0.0))
axis_p2 = Axis(start=Point2D(5.0, 0.0), end=Point2D(5.0, 4.0))

# Criação das paredes estruturais com amarração direta nas extremidades
wall_p1 = Wall(
    wall_id="P1",
    axis=axis_p1,
    thickness=0.14,
    start_bond=BondType.DIRECT,
    end_bond=BondType.DIRECT,
)

wall_p2 = Wall(
    wall_id="P2",
    axis=axis_p2,
    thickness=0.14,
    start_bond=BondType.DIRECT,
    end_bond=BondType.NONE,
)

# Criação da planta baixa e adição de porta
floor_plan = (
    FloorPlan(plan_id="PLAN_TIPO", height=2.80)
    .add_wall(wall_p1)
    .add_wall(wall_p2)
    .add_opening("P1", Opening(opening_id="PORTA_1", opening_type=OpeningType.DOOR, offset_along_wall=1.0, width=0.80, height=2.10))
)

print(f"Planta {floor_plan.plan_id}: {len(floor_plan.walls)} paredes, {floor_plan.total_wall_length:.2f} m total")
```

### 2. Análise de Tensões em Seção sob Flexo-Compressão (`mechanics` & `sections`)

```python
from pymasondesign.sections import RectangularSection
from pymasondesign.mechanics import SectionForces, MechanicsService

# Seção transversal de parede (14 cm x 300 cm)
section = RectangularSection(width=14.0, height=300.0)
properties = section.compute_properties()

# Esforços seccionais de cálculo (N em kN, M em kN.cm)
forces = SectionForces(normal=-450.0, moment_x=22500.0, moment_y=0.0)

# Cálculo do plano de tensões normais
plane = MechanicsService.calculate_normal_stress_plane(forces, properties)
sigma_min, sigma_max = MechanicsService.calculate_extreme_stresses(plane, properties)
regime = MechanicsService.classify_stress_regime(plane, properties)

print(f"Tensão mínima (compressão máxima): {sigma_min:.3f} kN/cm²")
print(f"Tensão máxima: {sigma_max:.3f} kN/cm²")
print(f"Regime de tensões: {regime.name}")
```

### 3. Consultando Materiais Normativos da NBR 16868 (`materials`)

```python
from pymasondesign.materials import NBR16868MasonryFactory, SteelSpecification

# Obtém automaticamente o compósito normativo para bloco de concreto fbk = 14 MPa
masonry_spec = NBR16868MasonryFactory.concrete_from_fbk(14.0)

print(f"Resistência prisma oco (fpk): {masonry_spec.fpk} MPa")
print(f"Resistência prisma grauteado (fpgk): {masonry_spec.fpgk} MPa")
print(f"Argamassa mínima recomendada (fa): {masonry_spec.mortar.fa} MPa")
print(f"Graute mínimo recomendado (fg): {masonry_spec.grout.fg} MPa")

# Especificação do aço CA-50
steel = SteelSpecification.ca50()
print(f"Resistência de cálculo fyd (gamma_s = 1.15): {steel.calculate_fyd(1.15):.2f} MPa")
```

---

## Execução de Testes

Execute a suíte de testes unitários:

```powershell
python -m unittest discover -s tests
```

---

## Licença

Este projeto está sob a licença MIT. Consulte o arquivo [LICENSE](LICENSE) para mais detalhes.
