# ALPHA MEDINA — Tech Engine Skills

## Overview

This directory contains the **20 ALPHA MEDINA Architecture-Based Tech Engine Skills** — a layered system of specialized capabilities built on the Medina Operating System doctrine.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│              ALPHA MEDINA SKILL ARCHITECTURE                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌─────────────────────────────────────────────────────────┐     │
│  │         CORE DOCTRINE / INTELLIGENCE LAYER               │     │
│  │  medina-operating-system · doctrine-synthesizer          │     │
│  │  worldview-expansion-engine · anti-drift-reviewer        │     │
│  │  mission-roadmap-orchestrator                            │     │
│  └────────────────────────────┬────────────────────────────┘     │
│                               │                                   │
│  ┌────────────────────────────▼────────────────────────────┐     │
│  │          CORE BRAIN / ENTITY TECH LAYER                  │     │
│  │  core-brain-architect · emergence-engineering-reviewer    │     │
│  │  entity-body-system-designer · npc-training-engine       │     │
│  │  synthetic-entity-productizer                            │     │
│  └────────────────────────────┬────────────────────────────┘     │
│                               │                                   │
│  ┌────────────────────────────▼────────────────────────────┐     │
│  │        COMPANY / MARKET / ORGANISM LAYER                 │     │
│  │  organism-company-builder · company-genesis-engine        │     │
│  │  market-genesis-strategist · moat-and-defense-architect   │     │
│  │  parallax-infrastructure-strategist                       │     │
│  └────────────────────────────┬────────────────────────────┘     │
│                               │                                   │
│  ┌────────────────────────────▼────────────────────────────┐     │
│  │       RESOURCE HUB / PUBLIC OUTPUT LAYER                 │     │
│  │  resource-hub-organizer · public-doctrine-writer         │     │
│  │  research-map-builder                                    │     │
│  └────────────────────────────┬────────────────────────────┘     │
│                               │                                   │
│  ┌────────────────────────────▼────────────────────────────┐     │
│  │       CONSTRUCTION / REAL-WORLD OPS LAYER                │     │
│  │  construction-estimating-reviewer · project-ops-chief    │     │
│  └─────────────────────────────────────────────────────────┘     │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

## Build Order

Skills are built in waves of 5. Each wave depends on the prior wave being complete.

### Wave 1: Master Operating Stack ✅ Built

| # | Skill | Purpose |
|---|-------|---------|
| 1 | `medina-operating-system` | Full cognitive operating framework |
| 2 | `anti-drift-reviewer` | Quality enforcement across all outputs |
| 3 | `doctrine-synthesizer` | Raw ideas → structured doctrine |
| 4 | `mission-roadmap-orchestrator` | Projects → roadmaps with gates and risks |
| 5 | `resource-hub-organizer` | Ideas → organized topics and release paths |

### Wave 2: Technical Core (Planned)

| # | Skill | Purpose |
|---|-------|---------|
| 6 | `core-brain-architect` | Brain-body synthetic cognition architecture |
| 7 | `emergence-engineering-reviewer` | Tests for real emergence vs generic AI |
| 8 | `entity-body-system-designer` | Entity body schemas and control layers |
| 9 | `synthetic-entity-productizer` | Engine → defense/robotics/gaming products |
| 10 | `organism-company-builder` | Company organisms and operating systems |

### Wave 3: Company / Market / Expansion (Planned)

| # | Skill | Purpose |
|---|-------|---------|
| 11 | `company-genesis-engine` | Vision → businesses, products, teams |
| 12 | `market-genesis-strategist` | Identifies new markets from doctrine |
| 13 | `moat-and-defense-architect` | Separates public from protected IP |
| 14 | `parallax-infrastructure-strategist` | AI-native finance/coordination infra |
| 15 | `worldview-expansion-engine` | Concept expansion across dimensions |

### Wave 4: Public Output / Real-World Ops (Planned)

| # | Skill | Purpose |
|---|-------|---------|
| 16 | `npc-training-engine` | NPC → training workflows and evaluation |
| 17 | `public-doctrine-writer` | Internal doctrine → public-safe outputs |
| 18 | `research-map-builder` | Questions → research maps and evidence |
| 19 | `construction-estimating-reviewer` | Scopes, bids, risk, and scheduling |
| 20 | `project-ops-chief` | Operations, communication, and sequencing |

## Skill Structure

Each skill contains:

```
skills/[skill-name]/
├── skill.yml          # Formal specification (input, output, connectors, dependencies)
└── instructions.md    # Operating instructions for the skill
```

## Critical Design Rule

Every skill must define three things before packaging:

1. **Input** — What the user gives it (raw idea, architecture draft, project scope, etc.)
2. **Output** — What it produces (roadmap, review, spec, doctrine map, report, etc.)
3. **Connectors/Tools** — What external systems it uses (files, GitHub, Drive, web, etc.)

## Dependency Graph

```
medina-operating-system
├── anti-drift-reviewer
│   ├── doctrine-synthesizer
│   │   ├── worldview-expansion-engine
│   │   ├── public-doctrine-writer
│   │   └── research-map-builder
│   ├── mission-roadmap-orchestrator
│   │   ├── resource-hub-organizer
│   │   ├── organism-company-builder
│   │   └── project-ops-chief
│   ├── core-brain-architect
│   │   ├── emergence-engineering-reviewer
│   │   ├── entity-body-system-designer
│   │   └── npc-training-engine
│   └── synthetic-entity-productizer
├── company-genesis-engine
├── market-genesis-strategist
├── moat-and-defense-architect
├── parallax-infrastructure-strategist
└── construction-estimating-reviewer
```

## Usage

Each skill's `instructions.md` provides the full operating protocol. The `skill.yml` provides the formal specification including input/output schemas and connector requirements.

To invoke a skill, provide it with the appropriate input type as defined in its `skill.yml` and expect the output format specified therein.
