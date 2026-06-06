# The Tripartite Synchronizer — Decision Guide

> How open-mind decides what needs thinking and what's muscle memory.

## Overview

The tripartite synchronizer is the decision engine at the heart of open-mind. For every function in your codebase, it answers one question: **should the LLM think about this, or is it automatic?**

## The Four Decisions

### HARDCODE — The Spinal Reflex

Your spinal cord pulls your hand off a hot stove before your brain knows it's hot. HARDCODE decisions are the same — the fastest possible path, no thinking required.

**When a function gets HARDCODE:**
- Called by 5+ other functions (it's a hot path)
- Has tests (verified correct)
- Is deterministic (same input → same output, always)
- Is safety-critical (failure is not an option)

**Example:** `add(a, b)` in a math library. It's tested 50 times, called by everything, and deterministic. Just run it.

**Cost:** 0 tokens, ~1ms, 100% deterministic.

### CACHED — The Cerebellar Pattern

Your cerebellum stores learned motor patterns. Riding a bike, typing on a keyboard — you're replaying cached sequences. CACHED decisions replay pre-computed results.

**When a function gets CACHED:**
- Output is deterministic and stable
- Expensive to compute, cheap to store
- On an edge device with limited compute
- Read-heavy (called often, rarely changes)

**Example:** `get_config()` returns the same config until someone changes it. Compute once, cache forever.

**Cost:** 0 tokens, ~5ms, 100% accurate to original computation.

### HYBRID — The Basal Ganglia Habit

Most of daily life is habit with occasional override. You drive home on autopilot but swerve when a dog runs into the road.

**When a function gets HYBRID:**
- Has a common case (cached) and edge cases (model)
- 70-90% test coverage (not fully verified)
- Deterministic in the common case, creative in edge cases

**Example:** `parse_natural_language(text)` works great for common patterns but needs the LLM for unusual phrasing.

**Cost:** ~50 tokens for edge cases, 0 tokens for cached path.

### MODEL — Prefrontal Deliberation

Your prefrontal cortex lights up for truly novel situations. This is expensive, slow, and creative — but it's where intelligence lives.

**When a function gets MODEL:**
- Novel (no cached pattern exists)
- Creative (multiple valid approaches)
- Untested (no verification history)
- Ambiguous (unclear what "correct" means)

**Example:** `generate_architecture(requirements)` — every time is different, creativity is the point.

**Cost:** ~500 tokens, ~2 seconds, quality depends on the model.

## The Three Inputs

### Hardware Profile — The Body

```python
from interpreter.induction import TriHardwareProfile, probe_hardware

# Auto-detect
hw_from_probe = TriHardwareProfile.from_hardware(probe_hardware())

# Manual
hw = TriHardwareProfile(
    compute_power=0.8,       # 0-1: how much compute is available
    gpu_available=True,      # GPU present?
    memory_gb=32.0,          # Available RAM
    battery_level=None,      # Battery % (None = plugged in)
    device_type="workstation"  # workstation, laptop, edge, mobile
)
```

**How it affects decisions:**
- High compute + GPU → favor HARDCODE (we can afford fast execution)
- Low compute + edge → favor CACHED (can't afford recomputation)
- Battery low → favor CACHED (minimize compute to save energy)

### Application Profile — The Task

```python
from interpreter.induction import TriApplicationProfile

app = TriApplicationProfile(
    latency_requirement_ms=10,     # How fast must this be?
    accuracy_requirement=0.95,     # How correct must this be? (0-1)
    safety_critical=True,          # Can errors hurt people?
    scale=1000,                    # How many invocations?
    deterministic=True,            # Must this be reproducible?
)
```

**How it affects decisions:**
- High safety + low latency → HARDCODE (must be fast AND correct)
- High accuracy + flexible latency → HYBRID (verify with model)
- Creative task + no safety → MODEL (let the LLM improvise)
- High scale + deterministic → HARDCODE (repetition rewards optimization)

### User Profile — The Human

```python
from interpreter.induction import TriUserProfile

user = TriUserProfile(
    wants_manual_control=False,   # User wants to approve each action?
    wants_creativity=0.2,         # 0=robot, 1=artist
    wants_consistency=0.9,        # 0=variety, 1=same every time
    tolerance_for_error=0.1,      # 0=zero mistakes, 1=ship it
)
```

**How it affects decisions:**
- High consistency + low error tolerance → HARDCODE/CACHED
- High creativity + tolerant → MODEL
- Manual control → HYBRID (ask before acting on edge cases)

## Pre-Built Scenarios

```python
from interpreter.induction.profiles import PROFILES

# Safety-critical autonomous system
hw, app, user = PROFILES["autonomous_driving"]
# → Most functions get HARDCODE

# Creative writing assistant
hw, app, user = PROFILES["creative_writing"]
# → Most functions get MODEL

# Edge sensor node
hw, app, user = PROFILES["edge_sensor"]
# → Most functions get CACHED

# Developer tool (balanced)
hw, app, user = PROFILES["developer_tool"]
# → Mix of HARDCODE and HYBRID
```

## Real-World Example

Ingesting the SuperInstance ternary fleet (303 Rust crates):

```
Total functions parsed: 6,000+

Decision breakdown:
  HARDCODE: 3,200 (53%) — math functions, tested hot paths
  CACHED:    800 (13%) — config lookups, stable outputs
  HYBRID:   1,500 (25%) — mostly deterministic, some edge cases
  MODEL:      500 (8%)  — creative generation, novel patterns

Muscle memory: 4,000 functions (67%) = 0 tokens each
Needs thinking: 2,000 functions (33%) = ~50-500 tokens each

Context savings: 4,000 × 250 = 1,000,000 tokens freed
That's 8× the GPT-4 context window, freed for actual thinking.
```
