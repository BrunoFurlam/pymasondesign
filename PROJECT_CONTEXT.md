# PyMasonDesign — Contexto do Projeto e Domínio

Este documento estabelece o contexto de negócio, domínio de engenharia estrutural, objetivos estratégicos e escopo do **PyMasonDesign**.

---

## 1. Visão Geral e Identidade

O **PyMasonDesign** é uma biblioteca *core* em Python de alta performance e rigor matemático, desenvolvida para modelagem, análise mecânica, dimensionamento e verificação de estruturas em **Alvenaria Estrutural** em conformidade com as normas técnicas brasileiras, primariamente a **ABNT NBR 16868 (Partes 1 a 3)**.

### Propósito
Fornecer um núcleo computacional desacoplado, imutável e altamente testável capaz de:
1. Representar a geometria e a topologia de plantas e edifícios em alvenaria estrutural.
2. Calcular propriedades geométricas e inércias de seções simples e compostas (incluindo abas colaborantes e homogeneização).
3. Realizar análises seccionais de tensões em regime elástico (flexo-compressão reta e oblíqua).
4. Gerenciar especificações normativas de materiais (blocos de concreto, blocos cerâmicos, argamassas, grautes e armaduras de aço).
5. Servir como motor (*engine*) para ferramentas externas: plugins CAD/BIM (como Autodesk Revit), aplicações web de cálculo, utilitários de linha de comando (CLI) e geradores de relatórios de memória de cálculo.

---

## 2. Domínio de Engenharia e Normas de Referência

O projeto implementa e segue estritamente as seguintes normas da ABNT (Associação Brasileira de Normas Técnicas):

- **ABNT NBR 16868-1:2020** — *Alvenaria estrutural — Parte 1: Projeto*:
  - Métodos de dimensionamento aos Estados Limites Últimos (ELU) e de Serviço (ELS).
  - Determinação das resistências características de projeto ($f_d, f_{vd}, f_{yd}$).
  - Coeficientes de redução por esbeltez ($m$ / $\phi$) e limites de esbeltez ($\lambda \le 24$ para paredes não armadas, $\lambda \le 30$ para armadas).
  - Flange / abas colaborantes em paredes com amarração direta e indireta.
  - Verificação de esforços de compressão, flexo-compressão, tração e cisalhamento em paredes de contraventamento.
- **ABNT NBR 16868-2:2020** — *Alvenaria estrutural — Parte 2: Execução e controle de obras*.
- **ABNT NBR 16868-3:2020** — *Alvenaria estrutural — Parte 3: Métodos de ensaio*.
- **ABNT NBR 6118:2023** — *Projeto de estruturas de concreto — Procedimento* (para critérios subsidiários de armaduras e grautes).
- **ABNT NBR 8681:2004** — *Ações e segurança nas estruturas — Procedimento*.

---

## 3. Notações e Convenções de Engenharia

### Grandezas e Unidades Típicas
| Grandeza | Unidades Sugeridas | Descrição |
| :--- | :--- | :--- |
| Comprimento / Espessura / Coordenadas | $\text{cm}$ ou $\text{m}$ | Dimensões de paredes, aberturas e seções |
| Área | $\text{cm}^2$ ou $\text{m}^2$ | Área bruta ($A$), área líquida ($A_n$) ou efetiva ($A_{ef}$) |
| Momento de Inércia | $\text{cm}^4$ ou $\text{m}^4$ | $I_{xx}, I_{yy}, I_{xy}, I_u, I_v$ |
| Força Normal ($N$) / Força Cortante ($V$) | $\text{kN}$ | Esforços seccionais |
| Momento Fletor ($M_x, M_y$) | $\text{kN}\cdot\text{cm}$ ou $\text{kN}\cdot\text{m}$ | Momentos fletores atuantes |
| Tensão ($\sigma, \tau$) / Resistência ($f_k, f_d$) | $\text{MPa}$ ($\text{kN/cm}^2 \times 10$) | Tensões normais, cisalhamento e resistências |
| Módulo de Elasticidade ($E, E_s$) | $\text{MPa}$ ou $\text{kN/cm}^2$ | Módulo de deformação longitudinal |

### Símbolos Normativos Principais
- $f_{bk}$: Resistência característica à compressão do bloco na área bruta ($\text{MPa}$).
- $f_a$: Resistência média à compressão da argamassa aos 28 dias ($\text{MPa}$).
- $f_g, f_{gk}$: Resistência característica à compressão do graute ($\text{MPa}$).
- $f_{pk}$: Resistência característica à compressão do prisma oco ($\text{MPa}$).
- $f_{pgk}$ ($f_{pk}^*$): Resistência característica à compressão do prisma cheio/grauteado ($\text{MPa}$).
- $f_k$: Resistência característica da alvenaria à compressão simples.
- $f_d = f_k / \gamma_m$: Resistência de cálculo da alvenaria.
- $f_{yk}, f_{yd}$: Resistência ao escoamento característica e de cálculo do aço.
- $\gamma_m, \gamma_s, \gamma_f$: Coeficientes de ponderação para alvenaria ($\gamma_m = 2.0$ para alvenaria não armada em geral, $1.65$ para armada sob controle rigoroso), aço ($\gamma_s = 1.15$) e ações ($\gamma_f = 1.4$).

---

## 4. Objetivos do Projeto e Roadmap

> [!NOTE]
> **Previsão e Flexibilidade de Escopo**: O roadmap a seguir representa um planejamento preliminar e uma estimativa de desenvolvimento. As fases, escopos e prioridades podem sofrer alterações, inclusões ou readequações conforme a evolução do projeto, requisitos práticos de integração (ex.: plugins BIM) e demandas de engenharia.

### Fase 1: Fundações Matemáticas, Geométricas e Seccionais (Concluída)
- [x] Motor geométrico 2D com tolerâncias numéricas centralizadas (`pymasondesign.geometry`).
- [x] Cálculo de propriedades de seção arbitrária e composta via Shoelace/Green e Steiner (`pymasondesign.sections`).
- [x] Formulação linear de tensões normais, regimes de solicitação e equilíbrio (`pymasondesign.mechanics`).
- [x] Modelos de materiais e tabelas normativas pré-carregadas da NBR 16868 (`pymasondesign.materials`).
- [x] Lançamento e topologia de pavimentos, plantas, paredes, aberturas e nós de encontro (`pymasondesign.drafting`).

### Fase 2: Conversão de Drafting para Modelo de Dimensionamento Estrutural (Em Andamento)
- [x] **Modelos e Serviços de Painéis de Alvenaria (`pymasondesign.elements`)**:
  - Implementação de `MasonryPanel` imutável com discretização automática por vãos de abertura e nós de encontro.
  - Implementação de `PanelGroup` e algoritmo de componentes conexas por amarração direta (`MasonryPanelService.group_panels_by_direct_bond`).
- [ ] **Determinação de Abas Colaborantes (Flanges)**:
  - Cálculo analítico de larguras efetivas de flange ($b_f$) em nós em L, T e Cruz (conforme ABNT NBR 16868-1 para amarração direta e indireta).
  - Composição de seções em L, T, U e I para análise de flexo-compressão e rigidez global.
- [ ] **Modelagem de Lintéis e Contravergas (Lintels / Spandrels / Coupling Beams)**:
  - Extração de vigas de acoplamento/lintéis sobre vãos e peitoris/contravergas sob janelas.
  - Definição de rigidez equivalente, geometria e vinculação aos painéis adjacentes.
- [ ] **Grafo Estrutural e Modelo de Análise Global**:
  - Geração de modelo de barras equivalentes / macroelementos de pórtico espacial para distribuição de ações verticais (cargas de piso/telhado) e horizontais (vento/desaprumo).
  - Vinculações entre pavimentos (`Story`) e nós estruturais.

### Fase 3: Verificações Normativas ao Estado Limite Último (ELU)
- [ ] Módulo `pymasondesign.design.compression`:
  - Cálculo do fator de redução por esbeltez $m$ em função de $\lambda = h_{ef} / t_{ef}$ e excentricidades.
  - Verificação de capacidade resistente à compressão simples e flexo-compressão de painéis simples e com abas.
- [ ] Módulo `pymasondesign.design.shear`:
  - Verificação ao cisalhamento de painéis e paredes de contraventamento não armadas ($f_{vk0} + 0.5\sigma_0$) e armadas.
  - Cálculo de armaduras de cisalhamento em treliça ou barras horizontais.
- [ ] Módulo `pymasondesign.design.lintels`:
  - Dimensionamento e verificação de lintéis / vergas e contravergas (flexão, cisalhamento e ancoragem).

### Fase 4: Detalhamento, Grauteamento e Estado Limite de Serviço (ELS)
- [ ] Lógica de modulação de blocos e distribuição de pontos de grauteamento.
- [ ] Verificação de tensões em serviço (limitação de fissuração e tensões de compressão).
- [ ] Cálculo de deformações e rigidez equivalente de paredes com aberturas.

### Fase 5: Interfaces, Interoperabilidade e Relatórios
- [ ] Exportação/importação para IFC e integração com extensões BIM / Revit.
- [ ] Gerador de memórias de cálculo detalhadas em Markdown, HTML e PDF com equações formatadas em LaTeX.
- [ ] Interface CLI rica para automação de dimensionamento.

---

## 5. Casos de Uso e Aplicações

1. **Back-end de Cálculo Estrutural**: Integração como biblioteca de cálculo para softwares de análise e dimensionamento de edifícios de alvenaria estrutural.
2. **Plugins para BIM/CAD**: Fornecimento da inteligência estrutural para ferramentas como Autodesk Revit, permitindo ler as paredes modeladas, detectar encontros, amarrações e validar a segurança estrutural instantaneamente.
3. **Automação de Engenharia e Estudos Paramétricos**: Otimização de espessuras de blocos, classes de resistência e posições de grauteamento através de scripts Python.
