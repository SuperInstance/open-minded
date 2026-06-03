"""End-to-end test: induce lever-runner using open-mind"""
import sys
sys.path.insert(0, '.')

from interpreter.induction.ingester import ingest
from interpreter.induction.vector_builder import VectorBuilder
from interpreter.induction.synchronizer import TripartiteSynchronizer, Decision
from interpreter.induction.profiles import TERMINAL_COMMANDS


def test_induce_lever_runner():
    # Ingest lever-runner (local path passed as target_dir, already exists)
    result = ingest(
        repo_url="local://lever-runner",
        target_dir="/home/phoenix/repos/lever-runner",
    )

    func_count = len(result.functions)
    class_count = len(result.classes)
    test_file_count = len(result.test_files)
    call_graph_edges = sum(len(v) for v in result.call_graph.values())

    print(f"Ingested: {func_count} functions, {class_count} classes")
    print(f"Test files: {test_file_count}")
    print(f"Call graph edges: {call_graph_edges}")

    # Build vectors
    builder = VectorBuilder()
    vectors = builder.build_all(result)
    print(f"Built {len(vectors)} dual-side vectors")

    # Run tripartite decisions on each function
    sync = TripartiteSynchronizer()
    hw, app, user = TERMINAL_COMMANDS
    decisions = {}
    for func in result.functions:
        d = sync.decide(hw, app, user)
        decisions[func.name] = d.value

    # Count decisions
    from collections import Counter
    counts = Counter(decisions.values())
    print(f"\nTripartite decisions for lever-runner:")
    for k, v in sorted(counts.items(), key=lambda x: -x[1]):
        print(f"  {k}: {v} functions")

    # Assert reasonable distribution
    assert func_count > 0
    assert len(vectors) > 0
    assert 'hardcode' in decisions.values()  # terminal commands should be hardcoded

    return result, vectors, decisions


if __name__ == "__main__":
    result, vectors, decisions = test_induce_lever_runner()
    print("\n✅ Induction of lever-runner complete")
