"""Test that open-mind connects to lever-runner and pincherOS."""

import json
import sqlite3
import tempfile
from pathlib import Path

from interpreter.induction.export_lever import export_lever_pack, export_lever_pack_batch
from interpreter.induction.export_nail import export_nail, export_nail_batch
from interpreter.induction.hardware_probe import probe_hardware, HardwareCapabilities
from interpreter.induction.synchronizer import Decision


# ---------------------------------------------------------------------------
# lever-runner export
# ---------------------------------------------------------------------------

def test_hardcode_export(tmp_path):
    """Export a hardcoded function as a lever-runner command."""
    db = str(tmp_path / "commands.db")
    rec = export_lever_pack(
        function_name="add_numbers",
        module_path="math.utils",
        args=["5", "3"],
        description="Add two numbers",
        db_path=db,
    )
    assert rec["decision"] == Decision.HARDCODE.value
    assert "python -m math.utils add_numbers 5 3" in rec["command"]

    # Verify row in SQLite
    conn = sqlite3.connect(db)
    rows = conn.execute("SELECT intent, command FROM commands").fetchall()
    conn.close()
    assert len(rows) == 1
    assert rows[0][0] == "add_numbers with 5 3"


def test_hardcode_export_batch(tmp_path):
    """Batch export multiple hardcoded functions."""
    db = str(tmp_path / "commands.db")
    entries = [
        {"function_name": "foo", "module_path": "mod.a", "description": "foo func"},
        {"function_name": "bar", "module_path": "mod.b", "args": ["x"], "description": "bar func"},
    ]
    results = export_lever_pack_batch(entries, db_path=db)
    assert len(results) == 2
    assert results[0]["decision"] == Decision.HARDCODE.value
    assert results[1]["command"].endswith("bar x")

    conn = sqlite3.connect(db)
    count = conn.execute("SELECT COUNT(*) FROM commands").fetchone()[0]
    conn.close()
    assert count == 2


# ---------------------------------------------------------------------------
# pincherOS .nail export
# ---------------------------------------------------------------------------

def test_cached_export(tmp_path):
    """Export a cached function as a .nail file."""
    out_dir = str(tmp_path / "nails")
    manifest = export_nail(
        function_name="lookup_constant",
        cached_output={"pi": 3.14159},
        description="Cached pi constant",
        export_dir=out_dir,
    )
    assert manifest["decision"] == Decision.CACHED.value
    assert manifest["output"] == {"pi": 3.14159}

    nail_file = Path(out_dir) / "lookup_constant.nail"
    assert nail_file.exists()
    data = json.loads(nail_file.read_text())
    assert data["function"] == "lookup_constant"
    assert data["format"] == "pincherOS-nail"


def test_cached_export_batch(tmp_path):
    """Batch export multiple cached decisions."""
    out_dir = str(tmp_path / "nails")
    entries = [
        {"function_name": "a", "cached_output": 1},
        {"function_name": "b", "cached_output": [2, 3]},
    ]
    results = export_nail_batch(entries, export_dir=out_dir)
    assert len(results) == 2
    assert (Path(out_dir) / "a.nail").exists()
    assert (Path(out_dir) / "b.nail").exists()


# ---------------------------------------------------------------------------
# hardware probe
# ---------------------------------------------------------------------------

def test_hardware_probe():
    """Auto-detect hardware and create a profile."""
    cap = probe_hardware()
    assert isinstance(cap, HardwareCapabilities)
    assert cap.cpu_cores >= 1
    assert cap.ram_gb >= 0
    assert cap.device_type in ("desktop", "edge", "mobile", "server")

    # Verify conversion to legacy HardwareProfile
    hp = cap.to_sync_profile()
    assert hp.gpu == cap.gpu
    assert hp.cpu_count == cap.cpu_cores
