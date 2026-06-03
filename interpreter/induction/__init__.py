"""Induction engine for open-mind.

Ingests GitHub repos and builds living, iterating vector models that enable
both induction (learning via vectors) and deduction (analytic reasoning).

Quick start:
    from interpreter.induction import ingest, spread
    result = ingest("https://github.com/user/repo")
    spread(result, continuous=True)
"""

from interpreter.induction.ingester import ingest, IngestResult, FunctionInfo, ClassInfo
from interpreter.induction.vector_builder import VectorBuilder, DualVector
from interpreter.induction.synchronizer import Synchronizer, SyncDecision, Decision, HardwareProfile
from interpreter.induction.spreader import Spreader
from interpreter.induction.export_lever import export_lever_pack, export_lever_pack_batch
from interpreter.induction.export_nail import export_nail, export_nail_batch
from interpreter.induction.hardware_probe import probe_hardware, HardwareCapabilities

__all__ = [
    "ingest", "IngestResult", "FunctionInfo", "ClassInfo",
    "VectorBuilder", "DualVector",
    "Synchronizer", "SyncDecision", "Decision", "HardwareProfile",
    "Spreader",
    "export_lever_pack", "export_lever_pack_batch",
    "export_nail", "export_nail_batch",
    "probe_hardware", "HardwareCapabilities",
]
