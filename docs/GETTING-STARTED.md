# Getting Started with open-mind

## For New Developers

### What is open-mind?

open-mind is [Open Interpreter](https://github.com/OpenInterpreter/open-interpreter) with a superpower: it can **ingest** codebases and **understand** them. Think of it as giving an LLM a map of your entire codebase before it starts helping you.

### 5-Minute Setup

```bash
# Clone and install
git clone https://github.com/SuperInstance/open-mind.git
cd open-mind
pip install -e .

# That's it. Start using it.
interpreter
```

### Your First Ingestion

```python
# In a Python session (or Jupyter notebook)
from interpreter.induction import ingest

# Ingest any repo
result = ingest("https://github.com/pallets/flask")

# What did we get?
print(f"Functions: {len(result.functions)}")
print(f"Classes: {len(result.classes)}")
print(f"Test files: {len(result.test_files)}")
print(f"Call graph edges: {sum(len(v) for v in result.call_graph.values())}")
```

### Explore What You Ingested

```python
# Show all functions
for func in result.functions[:10]:
    tested = "✅" if func.has_tests else "❌"
    print(f"  {tested} {func.module}.{func.name}{func.signature}")

# Show call graph
for caller, callees in list(result.call_graph.items())[:5]:
    print(f"  {caller} calls: {', '.join(callees[:3])}")

# Find untested functions
untested = [f for f in result.functions if not f.has_tests]
print(f"\n{len(untested)} untested functions:")
for f in untested[:5]:
    print(f"  {f.module}.{f.name}")
```

### Make Tripartite Decisions

```python
from interpreter.induction import TripartiteSynchronizer, TriHardwareProfile, TriApplicationProfile, TriUserProfile

sync = TripartiteSynchronizer()

# Setup: what hardware, what task, what user preference?
hw = TriHardwareProfile(compute_power=0.8, gpu_available=True)
app = TriApplicationProfile(latency_requirement_ms=10, safety_critical=True)
user = TriUserProfile(wants_consistency=0.9)

# Decide
decision = sync.decide(hw, app, user)
print(f"Decision: {decision.value}")
print(f"Reasoning: {decision.reasoning}")
```

### Run the Demos

```bash
# Full pipeline: ingest → vectors → decisions → export
python demo_full_pipeline.py https://github.com/SuperInstance/lever-runner

# Tripartite synchronizer showcase
python demo_tripartite.py
```

## For Data Scientists

### Using with Jupyter

The induction engine works great in notebooks:

```python
# In a Jupyter cell
from interpreter.induction import ingest, VectorBuilder

# Ingest your project
result = ingest("./my-ml-project")

# Build vectors for similarity search
builder = VectorBuilder()
for func in result.functions:
    builder.build_function_vectors(func, "local")

# Find similar functions
matches = builder.search_input("data preprocessing")
for m in matches:
    print(f"  {m.function_name}: {m.input_text[:80]}")
```

### Analyzing Test Coverage

```python
# What's tested vs untested?
tested = sum(1 for f in result.functions if f.has_tests)
total = len(result.functions)
print(f"Coverage: {tested}/{total} ({100*tested/total:.1f}%)")

# Which modules need more tests?
from collections import Counter
untested_by_module = Counter(f.module for f in result.functions if not f.has_tests)
for module, count in untested_by_module.most_common(10):
    print(f"  {module}: {count} untested functions")
```

## For Embedded Engineers

### Hardware Probe

```python
from interpreter.induction import probe_hardware

hw = probe_hardware()
print(f"""
Device:  {hw.device_type}
Arch:    {hw.arch}
CPU:     {hw.cpu_cores} cores
RAM:     {hw.ram_gb:.1f} GB
GPU:     {'✅ ' + hw.gpu_name if hw.gpu else '❌ none'}
""")
```

### Export for Edge Devices

```python
from interpreter.induction import export_nail, export_nail_batch

# Export cached results for your ESP32
cached_functions = [
    {"function_name": "read_config", "cached_output": '{"interval": 5000}', "description": "Sensor read interval"},
    {"function_name": "get_calibration", "cached_output": '{"offset": -1.2}', "description": "Calibration offset"},
]
manifests = export_nail_batch(cached_functions, export_dir="./esp32-cache/")
```

## For Agent Builders

### Connecting to the Standalone Package

The standalone [openmind](https://github.com/SuperInstance/openmind) package wraps the induction engine with muscle memory and cellular computation:

```python
# Install standalone
# pip install openmind

import openmind

# Ingest → Build muscle memory → Flex
result = openmind.ingest("./firmware")
mm = openmind.MuscleMemory.build(result)
reflex = mm.flex("spi_write", data=b"\x01\x02")
print(reflex.exec_strategy)  # "direct" — muscle memory
```

### Using the Rust Crates

For production agent systems, the Rust crates provide type-safe, high-performance implementations:

- [openmind-esp32-bridge](https://github.com/SuperInstance/openmind-esp32-bridge) — Serial/WS transport to ESP32
- [openmind-conductor](https://github.com/SuperInstance/openmind-conductor) — Multi-agent orchestration
- [openmind-mirror](https://github.com/SuperInstance/openmind-mirror) — Self-reflection and coherence

## Troubleshooting

### Import Errors

If you see `ImportError: cannot import name 'list_files_info' from 'huggingface_hub'`:
- This is from the old Open Interpreter dependency chain
- The induction engine doesn't use HuggingFace
- Use the induction modules directly: `from interpreter.induction import ...`

### Tree-sitter Not Found

Multi-language parsing requires tree-sitter:
```bash
pip install tree-sitter tree-sitter-python tree-sitter-rust tree-sitter-c tree-sitter-javascript
```

Without tree-sitter, only Python files are parsed. The engine still works — just with fewer languages.

### Slow Ingestion

For large repos, use a persistent clone directory:
```python
result = ingest("https://github.com/huge/repo", target_dir="./cached-clone")
```

Next time, it'll skip the clone step and just re-parse.

## Next Steps

- Read the [Induction Engine Guide](INDUCTION-ENGINE.md) for the full API reference
- Read the [Tripartite Guide](TRIPARTITE-GUIDE.md) to understand decision-making
- Check out [agent-knowledge](https://github.com/SuperInstance/agent-knowledge) for the a2a docs
- Try the [standalone openmind package](https://github.com/SuperInstance/openmind) for muscle memory + Jupyter integration
