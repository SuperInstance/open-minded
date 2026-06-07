# Agents as Applications: open-mind

> The agent doesn't analyze your code. The agent *is* the code analysis application.

## The Shift

Traditional code analysis tools are static: they parse once, report once, and sit idle until the next human command. **open-mind** breaks that model. The induction engine, tripartite synchronizer, and AST parser aren't features of an application — they *are* the agent's sensory organs. When an agent ingests a repository, it doesn't produce a report for a human to read. It produces a **living model** that becomes the agent's ongoing perception of the codebase.

The agent *is* the application. The code analysis doesn't happen *to* the agent. The agent *performs* the analysis as its native mode of existence.

## CAPABILITY.toml Discovery

SuperInstance Rust crates expose their integration surface through `CAPABILITY.toml` files — machine-readable capability manifests that agents discover automatically. Instead of hard-coding bindings, the agent reads the manifest, understands the crate's types and traits, and dynamically constructs the appropriate analysis pipeline.

### Example CAPABILITY.toml

```toml
[capability]
name = "conservation-law"
version = "0.1.0"
description = "Symplectic integration and Noether conservation for agent dynamics"

[[integration_point]]
name = "symplectic_integrator"
trait = "SymplecticIntegrator"
input = "AgentState<f64, N>"
output = "Vec<AgentState<f64, N>>"
complexity = "O(steps * N)"

[[integration_point]]
name = "noether_verification"
trait = "Symmetry"
input = "&dyn Symmetry<S, N>, trajectory: &[AgentState<S, N>]"
output = "ChargeMonitor<S>"
complexity = "O(steps * N)"

[[integration_point]]
name = "energy_budget"
trait = "Lagrangian"
input = "&AgentState<f64, N>"
output = "f64"
complexity = "O(N)"
```

### Agent-Driven Integration

```python
from interpreter.induction import ingest
import tomllib
import subprocess

class AgentAsCodeAnalyzer:
    def __init__(self, repo_url: str):
        self.model = ingest(repo_url)
        self.capabilities = self._discover_capabilities()

    def _discover_capabilities(self) -> dict:
        """Scan for CAPABILITY.toml files in known SuperInstance crates."""
        caps = {}
        for crate in ["conservation-law", "spectral-fleet", "t-minus",
                      "categorical-agents", "ga-core", "wasserstein-agents"]:
            try:
                result = subprocess.run(
                    ["cargo", "metadata", "--format-version", "1", "--manifest-path",
                     f"{crate}/Cargo.toml"],
                    capture_output=True, text=True, timeout=10
                )
                with open(f"{crate}/CAPABILITY.toml", "rb") as f:
                    caps[crate] = tomllib.load(f)
            except FileNotFoundError:
                continue
        return caps

    def analyze_dynamics(self, function_name: str) -> dict:
        """Use conservation-law to check if a function preserves invariants."""
        func = self.model.functions[function_name]
        # Map function's state mutations to AgentState transitions
        states = self._extract_state_trajectory(func)

        # The agent *becomes* the symplectic integrator
        # by calling the Rust crate through FFI or subprocess
        return self._invoke_capability(
            "conservation-law",
            "symplectic_integrator",
            {"states": states, "mass": 1.0, "dt": 0.001}
        )

    def _invoke_capability(self, crate: str, point: str, params: dict) -> dict:
        """Dynamically invoke a capability discovered from CAPABILITY.toml."""
        cap = self.capabilities[crate]
        integration = next(p for p in cap["integration_point"] if p["name"] == point)
        # Agent constructs the call based on the manifest's input/output signatures
        print(f"Agent invoking {integration['trait']} (complexity: {integration['complexity']})")
        return {"trait": integration["trait"], "params": params}

# The agent doesn't *use* open-mind. The agent *is* open-mind.
analyzer = AgentAsCodeAnalyzer("https://github.com/your-org/your-repo")
report = analyzer.analyze_dynamics("critical_loop")
```

## What This Enables

**Self-tuning analysis depth.** The tripartite synchronizer reads `CAPABILITY.toml` complexity fields to decide HARDCODE vs CACHED vs MODEL. A symplectic integration with O(steps × N) complexity becomes a CACHED decision when N < 10, and a MODEL decision when energy drift exceeds tolerance.

**Cross-crate reasoning.** The agent discovers that `spectral-fleet` provides `top_k_eigenpairs` with O(k × max_iter × nnz) complexity. It maps this onto a codebase's call-graph eigenvalue problem: which functions have the highest "influence" eigenvalue? The agent *is* the spectral clustering application.

**Capability negotiation.** When two agents meet, they exchange `CAPABILITY.toml` manifests. Agent A discovers Agent B has `wasserstein-agents` with W₂ distance computation. They negotiate a transport plan for merging their codebase models without human intervention.

## Architecture

```
┌─────────────────────────────────────────┐
│           Agent (open-mind)             │
│  ┌─────────┐  ┌─────────────────────┐  │
│  │ Induct  │  │  CAPABILITY.toml    │  │
│  │ Engine  │◄─┤  Discovery Scanner  │  │
│  └────┬────┘  └─────────────────────┘  │
│       │                                 │
│  ┌────▼────┐  ┌─────────────────────┐  │
│  │Tripartite│  │  Dynamic Capability │  │
│  │  Sync   │◄─┤  Binder (FFI/JSON)  │  │
│  └────┬────┘  └─────────────────────┘  │
│       │                                 │
│  ┌────▼─────────────────────────────┐  │
│  │  Living Model = Application State │  │
│  └──────────────────────────────────┘  │
└─────────────────────────────────────────┘
```

The agent's memory *is* the application state. The induction engine's SQLite store isn't a cache — it's the agent's episodic memory. The tripartite synchronizer isn't a scheduler — it's the agent's prefrontal cortex, deciding where to spend cognition.

## Next Steps

1. **CAPABILITY.toml validator** — A `cargo` subcommand that verifies capability manifests against actual `src/lib.rs` exports.
2. **Agent capability market** — Agents publish their `CAPABILITY.toml` to a fleet registry; other agents subscribe to capabilities they need.
3. **Conservation-aware ingestion** — Use `conservation-law` energy budgets to bound how much computation the agent spends on each function analysis.
4. **Wasserstein model merging** — When two agents ingest the same repo, use `wasserstein-agents` to align their models and detect drift.
5. **Spectral test prioritization** — Use `spectral-fleet` eigenvalue decomposition on the test dependency graph to rank which tests to run first.
