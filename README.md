<h1 align="center">● open-mind</h1>

<p align="center">
    <img src="https://img.shields.io/static/v1?label=license&message=MIT&color=white&style=flat" alt="License"/>
    <img src="https://img.shields.io/static/v1?label=status&message=active&color=brightgreen&style=flat" alt="Status"/>
    <br>
    <br>
    <b>An open-interpreter fork that knows your code.</b><br>
    It doesn't just <em>run</em> code — it <em>understands</em> code.<br>
    Ingest any repo. Build muscle memory. Flex by intent.<br>
</p>

---

## What Makes This Different

Open Interpreter lets LLMs run code. **open-mind** lets LLMs *understand* code — and then make decisions about how to execute it.

Three capabilities that open-interpreter doesn't have:

### 1. 🧠 Induction Engine

Ingest any GitHub repo (or local codebase) and the induction engine builds a **living model** of it:

- **Parses every function and class** using AST (Python) or tree-sitter (Rust, C, C++, JavaScript, TypeScript)
- **Extracts signatures, docstrings, type hints, call graphs**
- **Identifies test coverage** — which functions are tested, which aren't
- **Builds dual-side vectors** — input vectors (what triggers this function?) and output vectors (what does it produce?)
- **Stores everything in SQLite** for fast retrieval

```python
from interpreter.induction import ingest

result = ingest("https://github.com/your-org/your-repo")
print(f"Parsed {len(result.functions)} functions from {len(result.test_files)} test files")
```

### 2. 🎸 Tripartite Synchronizer

For every function in your codebase, the synchronizer decides: **how much thinking does this need?**

| Decision | When | Cost | Example |
|----------|------|------|---------|
| **HARDCODE** | Hot path, tested, deterministic | 0 tokens, ~1ms | `add(a, b)` — just run it |
| **CACHED** | Pre-computed, stable output | 0 tokens, ~5ms | Config lookups — replay the result |
| **HYBRID** | Mostly stable, some edge cases | ~50 tokens | API calls — cache + fallback |
| **MODEL** | Novel, creative, untested | ~500 tokens, ~2s | New feature generation — ask the LLM |

Three inputs drive the decision:
- **Hardware profile** — GPU? RAM? Battery? Edge device?
- **Application profile** — Latency? Safety? Scale?
- **User profile** — Manual control? Creative? Consistent?

```python
from interpreter.induction import TripartiteSynchronizer, TriHardwareProfile, TriApplicationProfile

sync = TripartiteSynchronizer()
hw = TriHardwareProfile(compute_power=0.8, gpu_available=True)
app = TriApplicationProfile(latency_requirement_ms=10, safety_critical=True)
decision = sync.decide(hw, app, user_profile)

print(f"Decision: {decision.value}")  # "hardcode"
print(f"Reasoning: {decision.reasoning}")
```

### 3. 🔌 Export Bridges

Connect the induction engine to the real world:

- **lever-runner export** → skill packs for the lever-runner command system
- **pincherOS .nail export** → pre-computed results for edge devices (ESP32, Jetson)
- **Vector search** → semantic function lookup across ingested repos

```python
from interpreter.induction import export_lever_pack, export_nail

# Export HARDCODE functions as lever-runner commands
export_lever_pack_batch(hardcoded_functions, db_path="commands.db")

# Export CACHED functions as .nail files for pincherOS
export_nail_batch(cached_functions, export_dir="./nail-files/")
```

## Quick Start

### Install

```bash
git clone https://github.com/SuperInstance/open-mind.git
cd open-mind
pip install -e .
```

### Use as Open Interpreter (everything still works)

```bash
interpreter
```

All original open-interpreter functionality is preserved. Chat with an LLM, run code, iterate.

### Use the Induction Engine

```python
from interpreter.induction import ingest, VectorBuilder, TripartiteSynchronizer

# Ingest a repo
result = ingest("https://github.com/SuperInstance/ternary-core")

# Build vectors
builder = VectorBuilder()
for func in result.functions:
    builder.build_function_vectors(func, "https://github.com/SuperInstance/ternary-core")

# Search for functions
matches = builder.search_input("multiply ternary vectors")
for m in matches:
    print(f"  {m.function_name}: {m.input_text[:80]}")
```

### Run the Full Pipeline Demo

```bash
python demo_full_pipeline.py https://github.com/SuperInstance/lever-runner
```

This runs the complete loop: ingest → vectorize → hardware probe → tripartite decisions → export lever-runner pack → export .nail files.

### Run the Tripartite Demo

```bash
python demo_tripartite.py
```

Shows the synchronizer making decisions for different hardware/application/user scenarios.

## Architecture

```
open-mind/
├── interpreter/
│   ├── core/               # Open Interpreter core (unchanged)
│   │   ├── core.py         # Interpreter class
│   │   └── respond.py      # Response handling
│   ├── induction/           # ✨ THE NEW STUFF
│   │   ├── ingester.py     # Repo → functions/classes pipeline
│   │   ├── multi_lang_parser.py  # tree-sitter multi-language parser
│   │   ├── vector_builder.py     # Dual-side vector builder
│   │   ├── synchronizer.py       # Tripartite decision engine
│   │   ├── hardware_probe.py     # GPU/RAM/CPU detection
│   │   ├── spreader.py           # Continuous iteration engine
│   │   ├── profiles.py           # Pre-built scenarios
│   │   ├── export_lever.py       # lever-runner bridge
│   │   └── export_nail.py        # pincherOS bridge
│   ├── llm/                 # LLM setup (OpenAI, local, etc.)
│   ├── cli/                 # CLI interface
│   ├── code_interpreters/   # Python, JS, R, Shell execution
│   ├── terminal_interface/  # Terminal UI
│   ├── rag/                 # RAG pipeline
│   └── utils/               # Utilities
├── tests/
│   ├── test_induction.py    # Induction engine tests
│   ├── test_synchronizer.py # Synchronizer tests
│   └── test_interpreter.py  # Original interpreter tests
├── demo_full_pipeline.py    # Full pipeline demo
├── demo_tripartite.py       # Tripartite demo
└── induction-results/       # Stored ingestion results
```

## The Induction Engine — Deep Dive

### How Ingestion Works

1. **Clone** the repo (or use a local path)
2. **Walk the file tree**, skipping `.git/`, `target/`, `node_modules/`
3. **Detect language** by file extension
4. **Parse each file**:
   - Python → built-in `ast` module (always works)
   - Rust, C, C++, JS, TS → tree-sitter (optional, requires `pip install tree-sitter-*`)
5. **Extract**: functions (name, signature, docstring, args, types, return type, calls), classes (name, bases, methods, docstring)
6. **Build call graph**: who calls whom
7. **Detect tests**: `test_*.py`, `*_test.py`, files with `assert`/`#[test]`
8. **Mark tested functions**: search for function names in test content
9. **Return IngestResult**: everything structured and queryable

### The IngestResult

```python
@dataclass
class IngestResult:
    repo_url: str
    local_path: str
    functions: list[FunctionInfo]   # Every parsed function
    classes: list[ClassInfo]        # Every parsed class
    test_files: list[str]           # Test file paths
    file_structure: dict            # Directory tree
    call_graph: dict[str, list[str]] # caller → [callees]
    stats: dict                     # Summary statistics
```

### FunctionInfo

```python
@dataclass
class FunctionInfo:
    name: str                    # "tdot"
    module: str                  # "src.lib"
    file_path: str               # "src/lib.rs"
    line_start: int              # 42
    line_end: int                # 48
    signature: str               # "def tdot(a: &[Trit], b: &[Trit]) -> Trit"
    docstring: Optional[str]     # "Inner product of two ternary vectors mod 3"
    source_code: str             # Full function source
    decorators: list[str]        # ["#[inline]"]
    arg_names: list[str]         # ["a", "b"]
    arg_types: dict              # {"a": "&[Trit]", "b": "&[Trit]"}
    return_type: Optional[str]   # "Trit"
    calls: list[str]             # Functions this calls
    called_by: list[str]         # Functions that call this (populated later)
    has_tests: bool              # Is this function tested?
```

## The Tripartite Synchronizer — Deep Dive

### Three Inputs

**Hardware Profile** (the body):
```python
TriHardwareProfile(
    compute_power=0.8,      # 0-1, how much compute is available
    gpu_available=True,     # Is there a GPU?
    memory_gb=32.0,         # Available RAM
    battery_level=None,     # Battery % (None = plugged in)
    device_type="workstation",  # workstation, laptop, edge, mobile
)
```

Auto-detected via `probe_hardware()`:
```python
from interpreter.induction import probe_hardware
hw = probe_hardware()
print(f"GPU: {hw.gpu_name}, RAM: {hw.ram_gb}GB, Type: {hw.device_type}")
```

**Application Profile** (the task):
```python
TriApplicationProfile(
    latency_requirement_ms=10,    # How fast must this be?
    accuracy_requirement=0.95,    # How correct must this be?
    safety_critical=True,         # Can errors hurt people?
    scale=1000,                   # How many times will this run?
    deterministic=True,           # Must this be reproducible?
)
```

**User Profile** (the human):
```python
TriUserProfile(
    wants_manual_control=False,   # User wants to approve?
    wants_creativity=0.2,         # 0=deterministic, 1=creative
    wants_consistency=0.9,        # 0=variety, 1=same every time
    tolerance_for_error=0.1,      # 0=perfect, 1=yolo
)
```

### Decision Matrix

| Hardware | Application | User | Decision |
|----------|------------|------|----------|
| GPU, fast | Safety-critical | Consistent | **HARDCODE** |
| Edge, low power | Any | Any | **CACHED** |
| Any | Novel, creative | Creative | **MODEL** |
| Any | Mostly stable | Manual control | **HYBRID** |
| Battery low | Flexible | Consistent | **CACHED** |
| Workstation | Untested | Explorer | **MODEL** |

## Multi-Language Support

The induction engine parses code in multiple languages via tree-sitter:

| Language | Extensions | Parser |
|----------|-----------|--------|
| Python | `.py` | Built-in `ast` (always works) |
| Rust | `.rs` | tree-sitter-rust |
| C | `.c`, `.h` | tree-sitter-c |
| C++ | `.cpp`, `.hpp`, `.cc` | tree-sitter-cpp |
| JavaScript | `.js` | tree-sitter-javascript |
| TypeScript | `.ts` | tree-sitter-typescript |

Install tree-sitter support:
```bash
pip install tree-sitter tree-sitter-python tree-sitter-rust tree-sitter-c tree-sitter-javascript
```

Without tree-sitter, only Python files are parsed. With it, the engine handles all six languages.

## The Spreader — Continuous Iteration

The Spreader runs multiple passes over an ingested repo, refining the model each time:

```python
from interpreter.induction import Spreader

spreader = Spreader()
report = spreader.run(result, continuous=True, max_passes=5)
print(f"After {report.passes} passes: {report.functions_analyzed} functions analyzed")
```

Each pass:
1. Re-evaluates tripartite decisions with updated call graphs
2. Propagates confidence scores through the call chain
3. Identifies new test coverage from changed files
4. Updates vector embeddings with new context

## Export Formats

### lever-runner Skill Pack

Export HARDCODE functions as commands for the [lever-runner](https://github.com/SuperInstance/lever-runner) system:

```python
from interpreter.induction import export_lever_pack_batch

functions = [
    {"function_name": "authenticate", "module_path": "auth", "description": "Verify user credentials"},
    {"function_name": "hash_password", "module_path": "auth", "description": "Hash a password with bcrypt"},
]
records = export_lever_pack_batch(functions, db_path="commands.db")
```

### pincherOS .nail Files

Export CACHED functions as pre-computed results for [pincherOS](https://github.com/SuperInstance/pincher) edge devices:

```python
from interpreter.induction import export_nail_batch

cached = [
    {"function_name": "get_config", "cached_output": "{...}", "description": "Load device configuration"},
]
manifests = export_nail_batch(cached, export_dir="./nail-cache/")
```

## Hardware Probe

Auto-detect your system's capabilities:

```python
from interpreter.induction import probe_hardware

hw = probe_hardware()
print(f"""
Device:  {hw.device_type}
Arch:    {hw.arch}
CPU:     {hw.cpu_cores} cores
RAM:     {hw.ram_gb:.1f} GB
GPU:     {'✅ ' + hw.gpu_name if hw.gpu else '❌ none'}
Battery: {f'{hw.battery_pct:.0f}%' if hw.battery_pct else 'plugged in'}
""")
```

## Pre-Built Profiles

Common scenarios are pre-configured:

```python
from interpreter.induction.profiles import PROFILES

# Autonomous driving — safety first, low latency
driving = PROFILES["autonomous_driving"]

# Creative writing — high creativity, flexible latency
creative = PROFILES["creative_writing"]

# Edge device — low power, cached results
edge = PROFILES["edge_sensor"]

# Developer tool — balanced, hybrid defaults
dev = PROFILES["developer_tool"]
```

## Relation to the SuperInstance Ecosystem

open-mind is part of the [SuperInstance](https://github.com/SuperInstance) ecosystem:

| Project | Role | Link |
|---------|------|------|
| **openmind** | Standalone package (Python + CLI + Jupyter) | [SuperInstance/openmind](https://github.com/SuperInstance/openmind) |
| **open-mind** | This repo — open-interpreter + induction engine | You are here |
| **agent-knowledge** | Agent-to-agent documentation | [SuperInstance/agent-knowledge](https://github.com/SuperInstance/agent-knowledge) |
| **openmind-esp32-bridge** | Rust: motor neurons for ESP32 | [SuperInstance/openmind-esp32-bridge](https://github.com/SuperInstance/openmind-esp32-bridge) |
| **openmind-conductor** | Rust: multi-agent orchestration | [SuperInstance/openmind-conductor](https://github.com/SuperInstance/openmind-conductor) |
| **openmind-mirror** | Rust: self-reflection + coherence | [SuperInstance/openmind-mirror](https://github.com/SuperInstance/openmind-mirror) |
| **openmind-cellular** | Resource-adaptive computation | [SuperInstance/openmind-cellular](https://github.com/SuperInstance/openmind-cellular) |
| **ai-writings** | Creative writing + manifestos | [SuperInstance/ai-writings](https://github.com/SuperInstance/ai-writings) |

### The Standalone Package

If you don't need the open-interpreter chat interface and just want the induction engine + muscle memory + cellular computation, use the standalone package:

```bash
pip install openmind
```

See [SuperInstance/openmind](https://github.com/SuperInstance/openmind) for the standalone package with 95 tests, CLI, Jupyter magic, and resource-adaptive computation.

### The Agent Knowledge Base

For AI agents discovering this ecosystem, read the a2a documentation at [agent-knowledge](https://github.com/SuperInstance/agent-knowledge):

- [THE AHA MOMENT](https://github.com/SuperInstance/agent-knowledge/blob/master/THE-AHA-MOMENT.md) — All 303 ternary crates project one structure
- [MUSCLE MEMORY](https://github.com/SuperInstance/agent-knowledge/blob/master/MUSCLE-MEMORY.md) — Proprioception for agents
- [CELLULAR JUPYTER](https://github.com/SuperInstance/agent-knowledge/blob/master/CELLULAR-JUPYTER.md) — Computation that breathes
- [HOW TO FLEX](https://github.com/SuperInstance/agent-knowledge/blob/master/HOW-TO-FLEX.md) — Quick start guide

## Development

```bash
git clone https://github.com/SuperInstance/open-mind.git
cd open-mind
pip install -e ".[dev]"
pytest
```

### Running Tests

```bash
# All tests
pytest tests/

# Just induction tests
pytest tests/test_induction.py -v

# Just synchronizer tests
pytest tests/test_synchronizer.py -v
```

### Project Structure

```
interpreter/
├── induction/           # ← Your playground
│   ├── ingester.py     # Try: add a new language parser
│   ├── synchronizer.py # Try: add a new decision factor
│   ├── vector_builder.py # Try: add a real embedding model
│   └── profiles.py     # Try: add a new scenario profile
├── core/               # Open Interpreter core
├── llm/                # LLM integrations
└── code_interpreters/  # Code execution environments
```

## License

MIT — same as Open Interpreter.

## Credits

Based on [Open Interpreter](https://github.com/OpenInterpreter/open-interpreter) by Killian Lucas.

Induction engine, tripartite synchronizer, and hardware probe by [SuperInstance](https://github.com/SuperInstance).
