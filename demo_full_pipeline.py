#!/usr/bin/env python3
"""
open-mind Full Pipeline Demo

Shows the complete loop:
1. Ingest a repo
2. Build dual-side vectors
3. Run tripartite synchronizer on each function
4. Export HARDCODE → lever-runner skill pack
5. Export CACHED → pincherOS .nail file
6. Print health report

Usage:
    python3 demo_full_pipeline.py /path/to/repo
    python3 demo_full_pipeline.py                          # defaults to lever-runner
"""

import os
import sys
import tempfile
from collections import Counter
from pathlib import Path

# ── ANSI colors ──────────────────────────────────────────────────────────
BOLD = "\033[1m"
DIM = "\033[2m"
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
MAGENTA = "\033[35m"
CYAN = "\033[36m"
WHITE = "\033[37m"
RESET = "\033[0m"

DECISION_COLORS = {
    "hardcode": GREEN,
    "model": MAGENTA,
    "hybrid": YELLOW,
    "cached": CYAN,
}

DECISION_ICONS = {
    "hardcode": "⚙️",
    "model": "🧠",
    "hybrid": "🔀",
    "cached": "📦",
}


def header(title: str):
    width = 60
    print()
    print(f"{BOLD}{BLUE}╔{'═' * width}╗{RESET}")
    print(f"{BOLD}{BLUE}║{title.center(width)}║{RESET}")
    print(f"{BOLD}{BLUE}╚{'═' * width}╝{RESET}")
    print()


def section(title: str):
    print(f"\n{BOLD}{CYAN}── {title} {'─' * max(0, 56 - len(title))}{RESET}")


def kv(key: str, value, indent: int = 2):
    print(f"{' ' * indent}{BOLD}{key}:{RESET} {value}")


def progress_bar(label: str, current: int, total: int, width: int = 30):
    pct = current / total if total else 1
    filled = int(width * pct)
    bar = "█" * filled + "░" * (width - filled)
    sys.stdout.write(f"\r  {label} [{GREEN}{bar}{RESET}] {current}/{total}")
    if current == total:
        sys.stdout.write("\n")
    sys.stdout.flush()


# ── Main pipeline ────────────────────────────────────────────────────────

def main():
    # Determine repo path
    default_url = "https://github.com/SuperInstance/lever-runner"
    repo_arg = sys.argv[1] if len(sys.argv) > 1 else default_url

    is_local = Path(repo_arg).is_dir()
    repo_url = repo_arg if not is_local else None
    repo_path = repo_arg if is_local else None

    header("open-mind Full Pipeline Demo")

    # ── Step 1: Ingest ───────────────────────────────────────────────────
    section("Step 1 — Ingest")
    print(f"  Source: {BOLD}{repo_url or repo_path}{RESET}")
    print(f"  Mode:   {'local directory' if is_local else 'GitHub clone'}")

    from interpreter.induction.ingester import ingest

    print(f"\n  {DIM}Ingesting...{RESET}")
    result = ingest(repo_url or f"file://{repo_path}", target_dir=repo_path)

    n_func = len(result.functions)
    n_class = len(result.classes)
    n_tests = len(result.test_files)
    n_edges = sum(len(f.calls) for f in result.functions)

    kv("Functions", f"{GREEN}{n_func}{RESET}")
    kv("Classes", f"{BLUE}{n_class}{RESET}")
    kv("Test files", f"{YELLOW}{n_tests}{RESET}")
    kv("Call-graph edges", f"{MAGENTA}{n_edges}{RESET}")

    # ── Step 2: Build vectors ────────────────────────────────────────────
    section("Step 2 — Build Dual-Side Vectors")

    from interpreter.induction.vector_builder import VectorBuilder

    builder = VectorBuilder()

    vectors = []
    for i, func in enumerate(result.functions):
        progress_bar("Vectorizing", i + 1, n_func)
        dv = builder.build_function_vectors(func, repo_url or str(repo_path))
        vectors.append(dv)

    n_input = sum(1 for v in vectors if v.input_vector)
    n_output = sum(1 for v in vectors if v.output_vector)

    kv("Input vectors", f"{GREEN}{n_input}{RESET}")
    kv("Output vectors", f"{CYAN}{n_output}{RESET}")

    # ── Step 3: Hardware probe ───────────────────────────────────────────
    section("Step 3 — Hardware Probe")

    from interpreter.induction.hardware_probe import probe_hardware

    hw = probe_hardware()
    kv("Device type", f"{BOLD}{hw.device_type}{RESET}")
    kv("Architecture", hw.arch)
    kv("CPU cores", hw.cpu_cores)
    kv("RAM", f"{hw.ram_gb:.1f} GB")
    kv("GPU", f"{'✅ ' + (hw.gpu_name or 'yes') if hw.gpu else '❌ no'}")
    if hw.gpu_vram_mb:
        kv("GPU VRAM", f"{hw.gpu_vram_mb} MiB")
    if hw.battery_pct is not None:
        kv("Battery", f"{hw.battery_pct:.0f}% ({'plugged' if hw.battery_plugged else 'on battery'})")

    # Build TriHardwareProfile from probe
    from interpreter.induction.synchronizer import TriHardwareProfile

    tri_hw = TriHardwareProfile(
        compute_power=0.5 if not hw.gpu else 0.8,
        gpu_available=hw.gpu,
        memory_gb=hw.ram_gb,
        battery_level=hw.battery_pct / 100.0 if hw.battery_pct else None,
        device_type=hw.device_type,
    )

    # ── Step 4: Tripartite decisions ─────────────────────────────────────
    section("Step 4 — Tripartite Synchronizer")

    from interpreter.induction.synchronizer import (
        TripartiteSynchronizer,
        TriApplicationProfile,
        TriUserProfile,
        Decision,
    )

    sync = TripartiteSynchronizer()

    # Default user profile
    user = TriUserProfile(
        wants_manual_control=True,
        wants_creativity=0.2,
        wants_consistency=0.9,
        tolerance_for_error=0.1,
    )

    decisions = {}
    for func in result.functions:
        qualified = f"{func.module}.{func.name}"

        # Build application profile per function based on its characteristics
        is_hot = len(func.called_by) >= 2
        app = TriApplicationProfile(
            latency_requirement_ms=10 if is_hot else 200,
            accuracy_requirement=0.95 if func.has_tests else 0.7,
            safety_critical=len(func.called_by) >= 5,
            scale=max(1, len(func.called_by) * 10),
            deterministic=is_hot,
        )

        d = sync.decide(tri_hw, app, user)
        decisions[qualified] = d

    # Distribution
    dist = Counter(d.value for d in decisions.values())

    print(f"\n  {BOLD}Decision Distribution:{RESET}")
    for decision_val in ("hardcode", "model", "hybrid", "cached"):
        count = dist.get(decision_val, 0)
        pct = count / len(decisions) * 100 if decisions else 0
        color = DECISION_COLORS.get(decision_val, WHITE)
        icon = DECISION_ICONS.get(decision_val, "?")
        bar_len = int(pct / 100 * 40)
        bar = "█" * bar_len + "░" * (40 - bar_len)
        print(f"  {icon} {color}{decision_val.upper():10s}{RESET} {count:4d} ({pct:5.1f}%) {color}{bar}{RESET}")

    # ── Step 5: Top connected functions ──────────────────────────────────
    section("Step 5 — Top 10 Most-Connected Functions")

    degree = Counter()
    for func in result.functions:
        qualified = f"{func.module}.{func.name}"
        deg = len(func.calls) + len(func.called_by)
        degree[qualified] = deg

    top10 = degree.most_common(10)
    for rank, (name, deg) in enumerate(top10, 1):
        d = decisions.get(name, Decision.HYBRID)
        color = DECISION_COLORS.get(d.value, WHITE)
        icon = DECISION_ICONS.get(d.value, "?")
        print(f"  {rank:2d}. {icon} {color}{name:50s}{RESET} degree={deg}  → {color}{d.value}{RESET}")

    # ── Step 6: Export HARDCODE → lever-runner ───────────────────────────
    section("Step 6 — Export HARDCODE → lever-runner pack")

    from interpreter.induction.export_lever import export_lever_pack_batch

    hardcoded = [
        {
            "function_name": qualified.rsplit(".", 1)[-1],
            "module_path": qualified.rsplit(".", 1)[0] if "." in qualified else qualified,
            "description": f"Auto-hardcoded by open-mind: {qualified}",
        }
        for qualified, d in decisions.items()
        if d == Decision.HARDCODE
    ]

    lever_db = os.path.join(tempfile.mkdtemp(), "commands.db")
    if hardcoded:
        records = export_lever_pack_batch(hardcoded, db_path=lever_db)
        kv("Exported", f"{GREEN}{len(records)}{RESET} lever-runner commands")
        kv("Database", lever_db)
        # Show first 3
        for rec in records[:3]:
            print(f"    {DIM}{rec['intent']}{RESET}")
        if len(records) > 3:
            print(f"    {DIM}... and {len(records) - 3} more{RESET}")
    else:
        print(f"  {YELLOW}No HARDCODE decisions to export.{RESET}")

    # ── Step 7: Export CACHED → .nail files ──────────────────────────────
    section("Step 7 — Export CACHED → pincherOS .nail files")

    from interpreter.induction.export_nail import export_nail_batch

    cached = [
        {
            "function_name": qualified.rsplit(".", 1)[-1],
            "cached_output": f"<pre-computed result for {qualified}>",
            "description": f"Auto-cached by open-mind: {qualified}",
        }
        for qualified, d in decisions.items()
        if d == Decision.CACHED
    ]

    nail_dir = tempfile.mkdtemp()
    if cached:
        manifests = export_nail_batch(cached, export_dir=nail_dir)
        kv("Exported", f"{CYAN}{len(manifests)}{RESET} .nail files")
        kv("Directory", nail_dir)
        for m in manifests[:3]:
            print(f"    {DIM}{m['function']}.nail{RESET}")
        if len(manifests) > 3:
            print(f"    {DIM}... and {len(manifests) - 3} more{RESET}")
    else:
        print(f"  {YELLOW}No CACHED decisions to export.{RESET}")

    # ── Summary ──────────────────────────────────────────────────────────
    header("Pipeline Complete")

    print(f"  {BOLD}Repo:{RESET}        {repo_url or repo_path}")
    print(f"  {BOLD}Functions:{RESET}    {n_func}")
    print(f"  {BOLD}Vectors:{RESET}      {n_input} input / {n_output} output")
    print(f"  {BOLD}Hardware:{RESET}     {hw.device_type} ({hw.arch}, {hw.ram_gb:.0f}GB RAM, {'GPU' if hw.gpu else 'no GPU'})")
    print(f"  {BOLD}Decisions:{RESET}    ", end="")
    print(" | ".join(
        f"{DECISION_COLORS.get(k, WHITE)}{DECISION_ICONS.get(k, '?')} {v} {k}{RESET}"
        for k, v in sorted(dist.items())
    ))
    print(f"  {BOLD}Lever pack:{RESET}  {len(hardcoded)} commands")
    print(f"  {BOLD}Nail files:{RESET}  {len(cached)} cached outputs")
    print()


if __name__ == "__main__":
    main()
