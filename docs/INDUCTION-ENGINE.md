# The Induction Engine — Developer Guide

> Ingest code. Build models. Decide execution strategy.

## What Is It?

The induction engine is open-mind's core innovation. It takes a codebase (any repo, any supported language) and produces a structured, queryable model of every function, class, and their relationships.

## The Pipeline

```
Source Code
    │
    ▼
File Discovery (walk directory tree)
    │
    ▼
Language Detection (.py → Python, .rs → Rust, etc.)
    │
    ▼
AST Parsing (ast module or tree-sitter)
    │
    ▼
Extraction (functions, classes, signatures, docstrings, call graphs)
    │
    ▼
Call Graph Resolution (who calls whom, reverse lookup)
    │
    ▼
Test Detection (heuristic: test_*.py, assert patterns)
    │
    ▼
IngestResult (structured data ready for queries)
```

## Data Structures

### FunctionInfo

The fundamental unit — everything the engine knows about one function.

```python
FunctionInfo(
    name="add",                        # Function name
    module="calculator.ops",           # Module path
    file_path="calculator/ops.py",     # Source file
    line_start=15,                     # Start line
    line_end=18,                       # End line
    signature="def add(a: int, b: int) -> int",
    docstring="Add two numbers.",      # Extracted docstring
    source_code="def add(a, b):\n...", # Full source
    decorators=["@cached"],            # Decorator names
    arg_names=["a", "b"],             # Argument names
    arg_types={"a": "int", "b": "int"}, # Type annotations
    return_type="int",                 # Return type annotation
    calls=["validate", "compute"],     # Functions this calls
    called_by=["multiply", "main"],    # Functions that call this
    has_tests=True,                    # Is this tested?
)
```

### ClassInfo

```python
ClassInfo(
    name="Calculator",
    module="calculator.core",
    file_path="calculator/core.py",
    line_start=5,
    line_end=45,
    docstring="A calculator with precision control.",
    source_code="class Calculator: ...",
    bases=["BaseCalculator"],
    methods=["add", "subtract", "multiply"],
)
```

### IngestResult

```python
IngestResult(
    repo_url="https://github.com/user/repo",
    local_path="/tmp/open-mind-ingest-xyz",
    functions=[...],          # list[FunctionInfo]
    classes=[...],            # list[ClassInfo]
    test_files=["test_ops.py"],
    file_structure={"": ["main.py", "ops.py"], "tests": ["test_ops.py"]},
    call_graph={"calculator.ops.add": ["validate"], ...},
    stats={"total_functions": 25, "total_classes": 3, "test_files": 1, ...},
)
```

## API Reference

### Ingestion

```python
from interpreter.induction import ingest, ingest_repo

# From GitHub URL
result = ingest("https://github.com/user/repo")

# From local path
result = ingest_repo("./my-local-project")

# With target directory
result = ingest("https://github.com/user/repo", target_dir="./cloned-repo")

# Cleanup after ingestion
result = ingest("https://github.com/user/repo", cleanup=True)
```

### Vector Building

```python
from interpreter.induction import VectorBuilder

builder = VectorBuilder(db_path="vectors.db")  # SQLite storage

# Build vectors for a function
dv = builder.build_function_vectors(func, repo_url="...")
# dv.input_vector: what triggers this function
# dv.output_vector: what this function produces

# Search
matches = builder.search_input("authentication", top_k=5)
matches = builder.search_output("returns user object", top_k=5)
matches = builder.search_generic("handle login", top_k=5)
```

### Tripartite Synchronizer

```python
from interpreter.induction import TripartiteSynchronizer, TriHardwareProfile, TriApplicationProfile, TriUserProfile

sync = TripartiteSynchronizer()

# Build profiles
hw = TriHardwareProfile(compute_power=0.8, gpu_available=True, memory_gb=32)
app = TriApplicationProfile(latency_requirement_ms=10, safety_critical=True)
user = TriUserProfile(wants_consistency=0.9, tolerance_for_error=0.1)

# Get decision
decision = sync.decide(hw, app, user)
print(decision.value)      # "hardcode"
print(decision.reasoning)  # Human-readable explanation
```

### Hardware Probe

```python
from interpreter.induction import probe_hardware

hw = probe_hardware()
print(hw.device_type)      # "workstation" | "laptop" | "edge" | "server"
print(hw.gpu)              # True/False
print(hw.gpu_name)         # "NVIDIA GeForce RTX 4090"
print(hw.gpu_vram_mb)      # 24564
print(hw.ram_gb)           # 31.4
print(hw.cpu_cores)        # 16
print(hw.arch)             # "x86_64"
print(hw.battery_pct)      # 85.0 or None
```

### Exports

```python
from interpreter.induction import export_lever_pack, export_nail

# Export to lever-runner
record = export_lever_pack(
    function_name="authenticate",
    module_path="auth.handlers",
    description="Verify user credentials against database",
    db_path="commands.db",
)

# Export to pincherOS .nail
manifest = export_nail(
    function_name="get_device_config",
    cached_output='{"theme": "dark", "lang": "en"}',
    description="Load device configuration from flash",
    export_dir="./nail-cache/",
)
```

### Spreader (Continuous Iteration)

```python
from interpreter.induction import Spreader

spreader = Spreader()
report = spreader.run(result, continuous=True, max_passes=5)

print(f"Passes: {report.passes}")
print(f"Functions analyzed: {report.functions_analyzed}")
print(f"Decisions updated: {report.decisions_updated}")
```

## Extending the Engine

### Adding a New Language

1. Install the tree-sitter grammar: `pip install tree-sitter-yourlang`
2. Add the extension to `LANG_MAP` in `multi_lang_parser.py`
3. Add the language import to `_get_language()`
4. The parser will automatically pick it up

### Adding a New Decision Factor

1. Add fields to `TriApplicationProfile` or `TriUserProfile`
2. Update the scoring logic in `TripartiteSynchronizer.decide()`
3. Add tests in `tests/test_synchronizer.py`

### Adding a New Export Format

1. Create `interpreter/induction/export_yourformat.py`
2. Follow the pattern from `export_lever.py` or `export_nail.py`
3. Export from `interpreter/induction/__init__.py`

## Testing

```bash
# Run all tests
pytest tests/

# Run just induction tests
pytest tests/test_induction.py -v

# Run with coverage
pytest tests/ --cov=interpreter.induction
```

## Performance

| Repo Size | Files | Parse Time | Full Pipeline |
|-----------|-------|-----------|---------------|
| Small (1-10) | 5 | 0.1s | 0.2s |
| Medium (10-100) | 50 | 0.5s | 1.0s |
| Large (100-1000) | 300 | 3s | 5s |
| Fleet (300+ repos) | 1000+ | 10s | 15s |

## Troubleshooting

### ImportError: cannot import name 'list_files_info' from 'huggingface_hub'

This is a known issue from the original open-interpreter dependency. The induction engine doesn't use HuggingFace — you can safely ignore this error when using only the induction modules.

### tree-sitter not found

The engine falls back to Python-only parsing if tree-sitter isn't installed. For multi-language support:
```bash
pip install tree-sitter tree-sitter-python tree-sitter-rust tree-sitter-c tree-sitter-javascript
```

### Large repos are slow

Use `target_dir` to clone to a persistent location (avoids re-cloning):
```python
result = ingest("https://github.com/huge/repo", target_dir="./cached-clone")
```
