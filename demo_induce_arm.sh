#!/bin/bash
# Demo script for ARM edge deployment
# Expected: most functions resolve to CACHED or HARDCODE
#
# Usage:
#   bash demo_induce_arm.sh [repo_url]

set -euo pipefail

REPO_URL="${1:-https://github.com/SuperInstance/lever-runner}"

echo "🔧 open-mind ARM Edge Demo"
echo "=========================="
echo ""

# ── Hardware detection ───────────────────────────────────────────────────
echo "📡 Probing hardware..."
python3 -c "
from interpreter.induction.hardware_probe import probe_hardware
hw = probe_hardware()
print(f'  Device:  {hw.device_type}')
print(f'  Arch:    {hw.arch}')
print(f'  RAM:     {hw.ram_gb:.1f} GB')
print(f'  CPU:     {hw.cpu_cores} cores')
print(f'  GPU:     {\"yes (\" + hw.gpu_name + \")\" if hw.gpu else \"no\"}')
if hw.battery_pct is not None:
    print(f'  Battery: {hw.battery_pct:.0f}%')
"
echo ""

# ── Induce with ARM profile ─────────────────────────────────────────────
echo "🔄 Inducing $REPO_URL with ARM edge profile..."
python3 -c "
import sys
from interpreter.induction.ingester import ingest
from interpreter.induction.vector_builder import VectorBuilder
from interpreter.induction.synchronizer import (
    TripartiteSynchronizer, TriApplicationProfile, TriUserProfile, Decision,
)
from interpreter.induction.profiles import HW_RASPBERRY_PI

# Ingest
result = ingest('$REPO_URL')
n_func = len(result.functions)
print(f'  Functions: {n_func}')
print(f'  Classes:   {len(result.classes)}')
print(f'  Tests:     {len(result.test_files)}')

# Build vectors
builder = VectorBuilder()
vectors = builder.build_all(result)
print(f'  Vectors:   {len(vectors)}')

# Run decisions with ARM hardware profile
sync = TripartiteSynchronizer()
user = TriUserProfile(
    wants_manual_control=False,
    wants_creativity=0.1,
    wants_consistency=0.95,
    tolerance_for_error=0.1,
)

from collections import Counter
decisions = {}
for func in result.functions:
    qualified = f'{func.module}.{func.name}'
    is_hot = len(func.called_by) >= 2
    app = TriApplicationProfile(
        latency_requirement_ms=10 if is_hot else 100,
        accuracy_requirement=0.9 if func.has_tests else 0.7,
        safety_critical=len(func.called_by) >= 5,
        scale=max(1, len(func.called_by) * 10),
        deterministic=is_hot,
    )
    d = sync.decide(HW_RASPBERRY_PI, app, user)
    decisions[qualified] = d

dist = Counter(d.value for d in decisions.values())
print()
print('  Decision distribution:')
for k in ('hardcode', 'model', 'hybrid', 'cached'):
    v = dist.get(k, 0)
    pct = v / len(decisions) * 100 if decisions else 0
    icons = {'hardcode': '⚙️', 'model': '🧠', 'hybrid': '🔀', 'cached': '📦'}
    bar = '█' * int(pct / 100 * 30) + '░' * (30 - int(pct / 100 * 30))
    print(f'    {icons.get(k, \"?\")} {k:10s} {v:4d} ({pct:5.1f}%) {bar}')

# Export
hardcoded = [q for q, d in decisions.items() if d == Decision.HARDCODE]
cached = [q for q, d in decisions.items() if d == Decision.CACHED]

if hardcoded:
    from interpreter.induction.export_lever import export_lever_pack_batch
    entries = [
        {'function_name': q.rsplit('.', 1)[-1], 'module_path': q.rsplit('.', 1)[0] if '.' in q else q}
        for q in hardcoded
    ]
    records = export_lever_pack_batch(entries)
    print(f'\n  ⚙️  Exported {len(records)} lever-runner commands')

if cached:
    from interpreter.induction.export_nail import export_nail_batch
    import tempfile
    nail_dir = tempfile.mkdtemp(prefix='open-mind-nail-')
    entries = [
        {'function_name': q.rsplit('.', 1)[-1], 'cached_output': f'<cached: {q}>'}
        for q in cached
    ]
    manifests = export_nail_batch(entries, export_dir=nail_dir)
    print(f'  📦 Exported {len(manifests)} .nail files → {nail_dir}')

print()
print('  ✅ ARM edge induction complete')
"

echo ""
echo "Done. On an actual ARM device, expect most functions to"
echo "resolve to HARDCODE or CACHED for maximum efficiency."
