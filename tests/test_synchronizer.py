"""Comprehensive tests for the Tripartite Synchronizer."""

import pytest
from interpreter.induction.synchronizer import (
    TripartiteSynchronizer,
    Decision,
    TriHardwareProfile,
    TriApplicationProfile,
    TriUserProfile,
)
from interpreter.induction.profiles import (
    GAMING_PC, DEV_LAPTOP, RASPBERRY_PI,
    CAR_BRAKE_SYSTEM, NPC_BEHAVIOR, TERMINAL_COMMANDS,
)


# ---- Helpers ----

def _hw(**overrides):
    defaults = dict(
        compute_power=0.5, gpu_available=False, memory_gb=8,
        battery_level=None, device_type="desktop",
    )
    defaults.update(overrides)
    return TriHardwareProfile(**defaults)


def _app(**overrides):
    defaults = dict(
        latency_requirement_ms=100, accuracy_requirement=0.8,
        safety_critical=False, scale=10, deterministic=False,
    )
    defaults.update(overrides)
    return TriApplicationProfile(**defaults)


def _user(**overrides):
    defaults = dict(
        wants_manual_control=False, wants_creativity=0.3,
        wants_consistency=0.5, tolerance_for_error=0.5,
        preference_override=None,
    )
    defaults.update(overrides)
    return TriUserProfile(**defaults)


# ---- User Override ----

class TestUserOverride:
    def test_override_hardcode(self):
        s = TripartiteSynchronizer()
        assert s.decide(_hw(), _app(), _user(preference_override="hardcode")) == Decision.HARDCODE

    def test_override_model(self):
        s = TripartiteSynchronizer()
        assert s.decide(_hw(), _app(), _user(preference_override="model")) == Decision.MODEL

    def test_override_hardcode_even_if_creative(self):
        s = TripartiteSynchronizer()
        assert s.decide(
            _hw(compute_power=1.0, gpu_available=True),
            _app(),
            _user(wants_creativity=0.99, preference_override="hardcode"),
        ) == Decision.HARDCODE

    def test_override_none_is_ignored(self):
        s = TripartiteSynchronizer()
        assert s.decide(_hw(), _app(), _user(preference_override=None)) == Decision.HYBRID


# ---- Safety Critical ----

class TestSafetyCritical:
    def test_safety_critical_always_hardcode(self):
        s = TripartiteSynchronizer()
        assert s.decide(_hw(), _app(safety_critical=True), _user()) == Decision.HARDCODE

    def test_safety_critical_with_model_override_user_wins(self):
        """User override is checked first, so model override beats safety."""
        s = TripartiteSynchronizer()
        result = s.decide(_hw(), _app(safety_critical=True), _user(preference_override="model"))
        assert result == Decision.MODEL

    def test_safety_critical_without_override(self):
        s = TripartiteSynchronizer()
        assert s.decide(_hw(), _app(safety_critical=True), _user()) == Decision.HARDCODE


# ---- Deterministic ----

class TestDeterministic:
    def test_deterministic_gives_hardcode(self):
        s = TripartiteSynchronizer()
        assert s.decide(_hw(), _app(deterministic=True), _user()) == Decision.HARDCODE

    def test_deterministic_not_safety_critical(self):
        s = TripartiteSynchronizer()
        assert s.decide(_hw(), _app(deterministic=True, safety_critical=False), _user()) == Decision.HARDCODE


# ---- Ultra-Low Latency ----

class TestUltraLowLatency:
    def test_low_latency_desktop_hardcode(self):
        s = TripartiteSynchronizer()
        assert s.decide(_hw(device_type="desktop"), _app(latency_requirement_ms=5), _user()) == Decision.HARDCODE

    def test_low_latency_edge_cached(self):
        s = TripartiteSynchronizer()
        assert s.decide(_hw(device_type="edge"), _app(latency_requirement_ms=5), _user()) == Decision.CACHED

    def test_low_latency_server_hardcode(self):
        s = TripartiteSynchronizer()
        assert s.decide(_hw(device_type="server"), _app(latency_requirement_ms=8), _user()) == Decision.HARDCODE


# ---- Creativity ----

class TestCreativity:
    def test_high_creativity_with_gpu(self):
        s = TripartiteSynchronizer()
        assert s.decide(
            _hw(gpu_available=True),
            _app(),
            _user(wants_creativity=0.8),
        ) == Decision.MODEL

    def test_high_creativity_with_compute_no_gpu(self):
        s = TripartiteSynchronizer()
        assert s.decide(
            _hw(compute_power=0.7, gpu_available=False),
            _app(),
            _user(wants_creativity=0.8),
        ) == Decision.MODEL

    def test_high_creativity_weak_hardware(self):
        s = TripartiteSynchronizer()
        assert s.decide(
            _hw(compute_power=0.3, gpu_available=False),
            _app(),
            _user(wants_creativity=0.8),
        ) == Decision.HYBRID

    def test_moderate_creativity_not_triggered(self):
        s = TripartiteSynchronizer()
        result = s.decide(_hw(), _app(), _user(wants_creativity=0.5))
        assert result == Decision.HYBRID


# ---- Consistency ----

class TestConsistency:
    def test_high_consistency_desktop(self):
        s = TripartiteSynchronizer()
        assert s.decide(
            _hw(device_type="desktop"),
            _app(),
            _user(wants_consistency=0.9),
        ) == Decision.HARDCODE

    def test_high_consistency_edge(self):
        s = TripartiteSynchronizer()
        assert s.decide(
            _hw(device_type="edge"),
            _app(),
            _user(wants_consistency=0.9),
        ) == Decision.CACHED


# ---- Manual Control ----

class TestManualControl:
    def test_manual_control_hardcode(self):
        s = TripartiteSynchronizer()
        assert s.decide(_hw(), _app(), _user(wants_manual_control=True)) == Decision.HARDCODE


# ---- High Accuracy + High Scale ----

class TestHighAccuracyScale:
    def test_accuracy_and_scale_hybrid(self):
        s = TripartiteSynchronizer()
        assert s.decide(
            _hw(),
            _app(accuracy_requirement=0.95, scale=200),
            _user(),
        ) == Decision.HYBRID

    def test_accuracy_only_not_enough(self):
        s = TripartiteSynchronizer()
        result = s.decide(_hw(), _app(accuracy_requirement=0.95, scale=10), _user())
        assert result == Decision.HYBRID

    def test_scale_only_not_enough(self):
        s = TripartiteSynchronizer()
        result = s.decide(_hw(), _app(accuracy_requirement=0.5, scale=500), _user())
        assert result == Decision.HYBRID


# ---- Edge + Low Battery ----

class TestEdgeLowBattery:
    def test_edge_low_battery(self):
        s = TripartiteSynchronizer()
        assert s.decide(
            _hw(device_type="edge", battery_level=0.2),
            _app(),
            _user(),
        ) == Decision.CACHED

    def test_edge_full_battery(self):
        s = TripartiteSynchronizer()
        result = s.decide(
            _hw(device_type="edge", battery_level=0.9),
            _app(),
            _user(),
        )
        assert result == Decision.HYBRID

    def test_desktop_low_battery_ignored(self):
        s = TripartiteSynchronizer()
        result = s.decide(
            _hw(device_type="desktop", battery_level=0.1),
            _app(),
            _user(),
        )
        assert result == Decision.HYBRID


# ---- Default Fallback ----

class TestDefaultFallback:
    def test_default_is_hybrid(self):
        s = TripartiteSynchronizer()
        assert s.decide(_hw(), _app(), _user()) == Decision.HYBRID


# ---- Batch ----

class TestBatch:
    def test_batch_decisions(self):
        s = TripartiteSynchronizer()
        paths = [GAMING_PC, DEV_LAPTOP, RASPBERRY_PI, CAR_BRAKE_SYSTEM]
        results = s.decide_batch(paths)
        assert len(results) == 4
        assert all(isinstance(d, Decision) for d in results)

    def test_batch_empty(self):
        s = TripartiteSynchronizer()
        assert s.decide_batch([]) == []


# ---- History / Recording ----

class TestRecording:
    def test_record_appends(self):
        s = TripartiteSynchronizer()
        s.record(_hw(), _app(), _user(), Decision.HARDCODE)
        assert len(s.history) == 1
        assert s.history[0]["decision"] == Decision.HARDCODE

    def test_decide_and_record(self):
        s = TripartiteSynchronizer()
        d = s.decide_and_record(_hw(), _app(safety_critical=True), _user())
        assert d == Decision.HARDCODE
        assert len(s.history) == 1


# ---- Pre-built Profile Scenarios ----

class TestPrebuiltProfiles:
    def test_gaming_pc(self):
        s = TripartiteSynchronizer()
        result = s.decide(*GAMING_PC)
        assert result == Decision.MODEL  # high creativity + GPU

    def test_dev_laptop(self):
        s = TripartiteSynchronizer()
        result = s.decide(*DEV_LAPTOP)
        assert result == Decision.HARDCODE  # deterministic=True

    def test_raspberry_pi(self):
        s = TripartiteSynchronizer()
        result = s.decide(*RASPBERRY_PI)
        assert result == Decision.HARDCODE  # deterministic=True

    def test_car_brake_system(self):
        s = TripartiteSynchronizer()
        result = s.decide(*CAR_BRAKE_SYSTEM)
        assert result == Decision.HARDCODE  # safety_critical + deterministic + low latency

    def test_npc_behavior(self):
        s = TripartiteSynchronizer()
        result = s.decide(*NPC_BEHAVIOR)
        assert result == Decision.MODEL  # wants_creativity=0.75 > 0.7 and gpu_available

    def test_terminal_commands(self):
        s = TripartiteSynchronizer()
        result = s.decide(*TERMINAL_COMMANDS)
        assert result == Decision.HARDCODE  # deterministic=True
