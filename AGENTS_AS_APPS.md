# Agents as Applications: Open-Mind as the Agent Brain

## Vision

Open-mind is the **interpreter that knows your code**. In the agents-as-applications paradigm, open-mind becomes the cognitive engine that:

1. **Scans** repositories for `CAPABILITY.toml` manifests
2. **Understands** what each SuperInstance crate does and how they connect
3. **Suggests** integrations based on what's already present
4. **Wires** crates together automatically

This transforms open-mind from a generic code interpreter into a **self-integrating agent brain** — it reads the ecosystem, discovers capabilities, and composes them.

## Architecture

```
┌─────────────────────────────────────────────────┐
│                  open-mind                       │
│              (Agent Brain)                       │
│                                                  │
│  ┌──────────────────┐  ┌──────────────────────┐ │
│  │ CapabilityScanner │  │  DependencyGraph     │ │
│  │                  │  │                      │ │
│  │ • scan_directory │→│  │ • topological_sort  │ │
│  │ • parse_manifest │  │ • transitive_deps    │ │
│  │ • find_integrations│  │ • dependents_of     │ │
│  └──────────────────┘  └──────────────────────┘ │
│           │                      │               │
│           ▼                      ▼               │
│  ┌─────────────────────────────────────────────┐ │
│  │         Integration Suggestions             │ │
│  │                                             │ │
│  │  • Required deps first (priority 0)         │ │
│  │  • Synergy matches next (priority 3)        │ │
│  │  • Optional enhancements last (priority 5)  │ │
│  └─────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────┘
         │ reads                    │ writes
         ▼                         ▼
  ┌──────────────┐        ┌──────────────────┐
  │ CAPABILITY   │        │ Cargo.toml       │
  │ .toml files  │        │ (auto-updated)   │
  └──────────────┘        └──────────────────┘
```

## Workflow: Scan → Discover → Suggest → Wire

### Step 1: Scan

```python
# The open-mind interpreter loads the capability scanner
from capability_discovery import CapabilityScanner

scanner = CapabilityScanner()
manifests = scanner.scan_directory("/path/to/project")
```

The scanner walks the directory tree, skipping `target/`, `.git/`, `node_modules/`, and hidden directories. Every `CAPABILITY.toml` is parsed into a `CapabilityManifest`.

### Step 2: Discover

```python
# Each manifest describes:
# - What the crate does (description, category)
# - What it needs (integrations with kind: required/optional)
# - What it provides (exports: typed symbols)

for m in manifests:
    print(f"{m.name} v{m.version}: {m.description}")
    for dep, spec in m.integrations.items():
        print(f"  → {dep} ({spec.kind}): {spec.reason}")
```

### Step 3: Suggest

```python
# Given what you already have, what should you add?
known = ["spectral-fleet", "conservation-law"]
suggestions = scanner.find_integrations(known)

for s in suggestions:
    print(f"[P{s.priority}] Add {s.crate_name}: {s.reason}")
    print(f"    Synergizes with: {', '.join(s.synergizes_with)}")
```

### Step 4: Wire

```python
# The agent brain takes the suggestions and modifies Cargo.toml,
# adds use declarations, and generates integration boilerplate.

graph = scanner.build_dependency_graph(manifests)
order = graph.topological_sort()  # Install in dependency order

for crate_name in order:
    wire_into_project(crate_name)
```

## CAPABILITY.toml Format

Every SuperInstance crate includes a `CAPABILITY.toml` in its root:

```toml
[capability]
name = "spectral-fleet"
version = "0.2.0"
description = "Eigenvalue-based agent ranking"
category = "analytics"

[capability.integrations]
fleet-warden = { kind = "optional", reason = "Feed fleet health into spectral ranking" }
conservation-law = { kind = "required", reason = "Energy budgets constrain eigenvalue computation" }

[capability.exports]
eigenvalues = "Vec<f64>"
rankings = "Vec<AgentRank>"
```

### Fields

| Field | Required | Description |
|-------|----------|-------------|
| `name` | ✅ | Unique crate name |
| `version` | ❌ | Semantic version (default: "0.0.0") |
| `description` | ❌ | Human-readable summary |
| `category` | ❌ | Tag: analytics, governance, physics, etc. |
| `integrations` | ❌ | Map of crate name → IntegrationSpec |
| `exports` | ❌ | Map of symbol name → type signature |

### IntegrationSpec

```toml
# Full form
fleet-warden = { kind = "optional", reason = "Why this integration exists" }

# Shorthand (kind only)
fleet-warden = "optional"
```

**Kinds:**
- `required` — Must be present for this crate to function
- `optional` — Enhances functionality when present
- `conflicts` — Cannot coexist with this crate

## SuperInstance Crate Ecosystem

```
                    fleet-warden
                   ╱            ╲
                  ╱              ╲
    conservation-law ─── spectral-fleet
              │                    │
              │                    │
        hodge-music          intention-field
              │                    │
              └────── room-topology
                          │
                      openrooms
```

## Integration with the Induction Engine

Open-mind's existing induction engine can be extended to:

1. **Induce from CAPABILITY.toml** — Learn crate patterns from manifest data
2. **Auto-generate integration code** — Use induced patterns to write wiring code
3. **Validate integrations** — Run the integration graph through the induction pipeline

## Getting Started

```bash
# Clone the ecosystem
git clone https://github.com/SuperInstance/open-mind
cd open-mind

# Run the capability scanner
cargo test src/capability_discovery.rs

# In Python, use the scanner via open-mind's interpreter
python -m interpreter "scan ./my-project for capabilities and suggest integrations"
```

## The Agent IS the Brain

The key insight: **the agent doesn't generate code to scan capabilities — it IS the scanner**. Open-mind with capability discovery becomes an agent that:

- Understands its own ecosystem
- Knows what capabilities exist and how they connect
- Can reason about missing integrations
- Auto-composes new agent configurations

This is agents-as-applications: the agent is not a tool-user, it IS the application.
