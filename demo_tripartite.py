#!/usr/bin/env python3
"""
Demo: Tripartite Synchronizer decision matrix in action.

Shows how the synchronizer routes different scenarios to
HARDCODE, MODEL, HYBRID, or CACHED based on hardware + app + user profiles.
"""

from interpreter.induction.synchronizer import (
    TripartiteSynchronizer, Decision,
    TriHardwareProfile, TriApplicationProfile, TriUserProfile,
)
from interpreter.induction.profiles import (
    GAMING_PC, DEV_LAPTOP, RASPBERRY_PI,
    CAR_BRAKE_SYSTEM, NPC_BEHAVIOR, TERMINAL_COMMANDS,
)


def label(decision: Decision) -> str:
    return {
        Decision.HARDCODE: "⚙️  HARDCODE (lever-runner)",
        Decision.MODEL:    "🧠 MODEL (LLM inference)",
        Decision.HYBRID:   "🔀 HYBRID (cache + model)",
        Decision.CACHED:   "📦 CACHED (pincherOS .nail)",
    }[decision]


def show(name: str, hw, app, user, sync: TripartiteSynchronizer):
    d = sync.decide(hw, app, user)
    print(f"\n{'─'*60}")
    print(f"  {name}")
    print(f"{'─'*60}")
    print(f"  Hardware : {hw.device_type} | compute={hw.compute_power:.2f} | gpu={hw.gpu_available} | ram={hw.memory_gb}GB")
    if hw.battery_level is not None:
        print(f"  Battery  : {hw.battery_level*100:.0f}%")
    print(f"  App      : latency≤{app.latency_requirement_ms}ms | accuracy={app.accuracy_requirement:.2f} | safety={app.safety_critical} | det={app.deterministic}")
    print(f"  User     : creativity={user.wants_creativity:.2f} | consistency={user.wants_consistency:.2f} | control={user.wants_manual_control}")
    if user.preference_override:
        print(f"  Override : {user.preference_override}")
    print(f"  ─────────────────────────────────")
    print(f"  Decision : {label(d)}")
    return d


def main():
    sync = TripartiteSynchronizer()

    print("╔══════════════════════════════════════════════════════════╗")
    print("║     TRIPARTITE SYNCHRONIZER — Decision Matrix Demo      ║")
    print("╚══════════════════════════════════════════════════════════╝")

    scenarios = [
        ("Gaming PC — Creative Rendering", *GAMING_PC),
        ("Dev Laptop — Tooling (lever-runner)", *DEV_LAPTOP),
        ("Raspberry Pi — IoT Sensor", *RASPBERRY_PI),
        ("Car ECU — Brake System (safety-critical)", *CAR_BRAKE_SYSTEM),
        ("Cloud Server — NPC Behavior", *NPC_BEHAVIOR),
        ("Dev Laptop — Terminal Commands", *TERMINAL_COMMANDS),
    ]

    decisions = []
    for name, hw, app, user in scenarios:
        d = show(name, hw, app, user, sync)
        decisions.append((name, d))

    print("\n\n╔══════════════════════════════════════════════════════════╗")
    print("║                  Edge Case Demos                        ║")
    print("╚══════════════════════════════════════════════════════════╝")

    show(
        "Edge Device — Low Battery (15%)",
        TriHardwareProfile(compute_power=0.1, gpu_available=False, memory_gb=2, battery_level=0.15, device_type="edge"),
        TriApplicationProfile(latency_requirement_ms=100, accuracy_requirement=0.8, safety_critical=False, scale=50, deterministic=False),
        TriUserProfile(wants_manual_control=False, wants_creativity=0.2, wants_consistency=0.6, tolerance_for_error=0.4),
        sync,
    )

    show(
        "Production API — High Scale & Accuracy",
        TriHardwareProfile(compute_power=0.8, gpu_available=True, memory_gb=64, battery_level=None, device_type="server"),
        TriApplicationProfile(latency_requirement_ms=50, accuracy_requirement=0.95, safety_critical=False, scale=10000, deterministic=False),
        TriUserProfile(wants_manual_control=False, wants_creativity=0.1, wants_consistency=0.7, tolerance_for_error=0.2),
        sync,
    )

    show(
        "User Forces Model — Despite Deterministic App",
        TriHardwareProfile(compute_power=0.3, gpu_available=False, memory_gb=4, battery_level=None, device_type="desktop"),
        TriApplicationProfile(latency_requirement_ms=200, accuracy_requirement=0.9, safety_critical=False, scale=1, deterministic=True),
        TriUserProfile(wants_manual_control=False, wants_creativity=0.5, wants_consistency=0.5, tolerance_for_error=0.5, preference_override="model"),
        sync,
    )

    print("\n\n╔══════════════════════════════════════════════════════════╗")
    print("║                     Summary                             ║")
    print("╚══════════════════════════════════════════════════════════╝")
    for name, d in decisions:
        print(f"  {d.value:10s} ← {name}")

    print(f"\n  Total decisions: {len(decisions)}")
    counts = {}
    for _, d in decisions:
        counts[d.value] = counts.get(d.value, 0) + 1
    for k, v in sorted(counts.items()):
        print(f"    {k}: {v}")


if __name__ == "__main__":
    main()
