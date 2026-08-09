# Diretrizes e Instruções de Desenvolvimento para Agentes de IA e Engenheiros

Este documento contém as diretrizes mandatórias de desenvolvimento para o repositório **PyMasonDesign**. Todos os agentes de IA e desenvolvedores devem seguir estritamente estas regras.

---

## 1. Princípios de Engenharia de Software

1. **Imutabilidade com `attrs`**:
   - Todas as classes de domínio (`Point2D`, `Axis`, `Wall`, `FloorPlan`, `NormalStressPlane`, etc.) DEVEM usar o decorator `@define` ou `@frozen` da biblioteca `attrs`.
   - Modificações de estado DEVEM retornar novas instâncias utilizando métodos cujos nomes expressem explicitamente a intenção de domínio (ex.: `floor_plan.add_wall(...)`, `floor_plan.add_opening(...)`, `axis.translated(...)`, `axis.reversed(...)`), evitando nomes genéricos com prefixo `with_...`.
   - NUNCA atribua valores a atributos de instâncias existentes (`obj.attr = value` é proibido).

2. **Tipagem Estrita e Python Moderno**:
   - Todo arquivo Python deve iniciar com `from __future__ import annotations`.
   - Todas as funções, métodos e atributos DEVEM ter type hints completos (`tuple`, `dict`, `float | None`, etc.).
   - Evite `Any`; use tipos genéricos ou protocolos tipados se necessário.

3. **Tolerâncias Numéricas e Comparações Geométricas**:
   - NUNCA compare números de ponto flutuante diretamente com `==` ou `!=` para posições, distâncias, áreas ou ângulos.
   - SEMPRE utilize as funções e constantes de `pymasondesign.geometry.tolerances`:
     - `is_close(a, b, tolerance)`
     - `is_zero(value, tolerance)`
     - `is_within_unit(t, tolerance)`
     - `is_at_vertex(t, tolerance)`
     - `is_interior(t, tolerance)`

4. **Conformidade com a Norma ABNT NBR 16868**:
   - Mantenha estrita fidelidade às equações e limites normativos (coeficientes de ponderação, tabelas de prismas e blocos, resistências de cálculo).
   - Documente nas docstrings o item específico da norma quando implementar fórmulas regulamentares (ex.: *ABNT NBR 16868-1:2020, Item 11.2*).

---

## 2. Padrões de Testes e Execução

1. **Cobertura Completa de Testes**:
   - Toda nova funcionalidade, classe ou método público DEVE ter testes unitários correspondentes em `tests/`.
   - Teste sempre os casos de borda: valores limites ($t=0, t=1$), tolerâncias de encontro, entradas inválidas que devem levantar `ValueError`, paredes colineares, etc.

2. **Como Executar a Suíte de Testes**:
   - No ambiente virtual local:
     ```powershell
     .\env\python.exe -m unittest discover -s tests
     ```
   - Ou utilizando `pytest` (se disponível no ambiente):
     ```powershell
     pytest
     ```

---

## 3. Estrutura de Diretórios e Nomenclatura

```text
src/pymasondesign/
├── geometry/       # Primitivas vetoriais 2D, eixos, transformações e tolerâncias
├── sections/       # Seções transversais estruturais, inércias e componentes compostos
├── mechanics/      # Análise de tensões, flexo-compressão biaxial e esforços seccionais
├── materials/      # Especificação de materiais e compósitos (blocos, argamassa, graute, aço)
├── drafting/       # Lançamento estrutural de pavimentos, paredes, vãos e encontros
└── structure/      # Modelo analítico estrutural (BuildingModel, StoryModel, FloorPlanModel, painéis e grupos)
```

- Nomes de arquivos: `snake_case.py`
- Nomes de classes: `PascalCase`
- Nomes de funções e variáveis: `snake_case`
- Constantes: `UPPER_SNAKE_CASE`
