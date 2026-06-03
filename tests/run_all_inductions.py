"""Run induction on all three repos and save results."""
import sys
sys.path.insert(0, '.')

import json
import os
from collections import Counter
from dataclasses import asdict
from datetime import datetime

from interpreter.induction.ingester import ingest
from interpreter.induction.vector_builder import VectorBuilder
from interpreter.induction.synchronizer import TripartiteSynchronizer, Decision
from interpreter.induction.profiles import TERMINAL_COMMANDS


def run_induction(name, repo_path):
    """Run full induction pipeline on a local repo."""
    print(f"\n{'='*60}")
    print(f"Inducing: {name}")
    print(f"Path: {repo_path}")
    print(f"{'='*60}")

    result = ingest(
        repo_url=f"local://{name}",
        target_dir=repo_path,
    )

    func_count = len(result.functions)
    class_count = len(result.classes)
    test_file_count = len(result.test_files)
    call_graph_edges = sum(len(v) for v in result.call_graph.values())

    print(f"Functions: {func_count}")
    print(f"Classes: {class_count}")
    print(f"Test files: {test_file_count}")
    print(f"Call graph edges: {call_graph_edges}")

    # Build vectors
    builder = VectorBuilder()
    vectors = builder.build_all(result)
    print(f"Vectors: {len(vectors)}")

    # Run tripartite decisions
    sync = TripartiteSynchronizer()
    hw, app, user = TERMINAL_COMMANDS
    decisions = {}
    for func in result.functions:
        d = sync.decide(hw, app, user)
        decisions[func.name] = d.value

    counts = Counter(decisions.values())
    print(f"Decisions: {dict(counts)}")

    # File types
    file_types = Counter()
    for files in result.file_structure.values():
        for f in files:
            ext = os.path.splitext(f)[1] or 'no-ext'
            file_types[ext] += 1
    print(f"File types: {dict(file_types.most_common(10))}")

    return result, vectors, decisions


def save_results(name, result, vectors, decisions, output_base):
    """Save induction results to files."""
    out_dir = os.path.join(output_base, name)
    os.makedirs(out_dir, exist_ok=True)

    # functions.json
    funcs_data = []
    for f in result.functions:
        fd = {
            'name': f.name,
            'module': f.module,
            'file_path': f.file_path,
            'line_start': f.line_start,
            'line_end': f.line_end,
            'signature': f.signature,
            'docstring': f.docstring,
            'decorators': f.decorators,
            'arg_names': f.arg_names,
            'arg_types': f.arg_types,
            'return_type': f.return_type,
            'calls': f.calls,
            'called_by': f.called_by,
            'has_tests': f.has_tests,
        }
        funcs_data.append(fd)
    with open(os.path.join(out_dir, 'functions.json'), 'w') as fp:
        json.dump(funcs_data, fp, indent=2, default=str)

    # vectors.json
    vecs_data = []
    for v in vectors:
        vecs_data.append({
            'function_name': v.function_name,
            'module': v.module,
            'input_text': v.input_text,
            'output_text': v.output_text,
            'input_vector_dim': len(v.input_vector),
            'output_vector_dim': len(v.output_vector),
        })
    with open(os.path.join(out_dir, 'vectors.json'), 'w') as fp:
        json.dump(vecs_data, fp, indent=2)

    # decisions.json
    with open(os.path.join(out_dir, 'decisions.json'), 'w') as fp:
        json.dump(decisions, fp, indent=2)

    # summary.md
    counts = Counter(decisions.values())
    file_types = Counter()
    for files in result.file_structure.values():
        for f in files:
            ext = os.path.splitext(f)[1] or 'no-ext'
            file_types[ext] += 1

    summary = f"""# Induction Report: {name}

Generated: {datetime.now().isoformat()}
Repo path: {result.local_path}

## Statistics

| Metric | Value |
|--------|-------|
| Functions | {len(result.functions)} |
| Classes | {len(result.classes)} |
| Test files | {len(result.test_files)} |
| Tested functions | {sum(1 for f in result.functions if f.has_tests)} |
| Call graph edges | {sum(len(v) for v in result.call_graph.values())} |
| Vectors built | {len(vectors)} |

## Tripartite Decisions

"""
    for k, v in sorted(counts.items(), key=lambda x: -x[1]):
        summary += f"- **{k}**: {v} functions\n"

    summary += f"""
## File Types

"""
    for ext, count in file_types.most_common(10):
        summary += f"- `{ext}`: {count} files\n"

    # Top called functions
    summary += "\n## Most-Connected Functions\n\n"
    by_calls = sorted(result.functions, key=lambda f: len(f.calls), reverse=True)[:10]
    for f in by_calls:
        summary += f"- `{f.name}` ({f.module}): calls {len(f.calls)} functions\n"

    # Test coverage
    summary += f"\n## Test Coverage\n\n"
    summary += f"- Tested: {sum(1 for f in result.functions if f.has_tests)}/{len(result.functions)} "
    summary += f"({100*sum(1 for f in result.functions if f.has_tests)/max(len(result.functions),1):.1f}%)\n"

    with open(os.path.join(out_dir, 'summary.md'), 'w') as fp:
        fp.write(summary)

    print(f"Saved results to {out_dir}")
    return summary


def main():
    output_base = os.path.expanduser('~/repos/open-minded/induction-results')
    os.makedirs(output_base, exist_ok=True)

    repos = [
        ("lever-runner", "/home/phoenix/repos/lever-runner"),
        ("pincherOS", "/home/phoenix/repos/pincherOS"),
        ("intelligent-terminal", "/home/phoenix/repos/intelligent-terminal"),
    ]

    summaries = {}
    for name, path in repos:
        if not os.path.exists(path):
            print(f"SKIP: {path} does not exist")
            continue
        result, vectors, decisions = run_induction(name, path)
        summary = save_results(name, result, vectors, decisions, output_base)
        summaries[name] = {
            'functions': len(result.functions),
            'classes': len(result.classes),
            'test_files': len(result.test_files),
            'vectors': len(vectors),
            'decisions': Counter(decisions.values()),
            'file_structure_files': sum(len(v) for v in result.file_structure.values()),
        }

    # Write SUMMARY.md
    write_overall_summary(output_base, summaries)
    print("\n✅ All inductions complete")


def write_overall_summary(output_base, summaries):
    path = os.path.join(output_base, 'SUMMARY.md')
    now = datetime.now().isoformat()

    lines = [
        f"# Induction Results Summary",
        f"",
        f"Generated: {now}",
        f"",
        f"## Overview",
        f"",
        f"| Repo | Functions | Classes | Test Files | Vectors | Decisions |",
        f"|------|-----------|---------|------------|---------|-----------|",
    ]

    for name, s in summaries.items():
        dec_str = ", ".join(f"{k}:{v}" for k, v in sorted(s['decisions'].items()))
        lines.append(f"| {name} | {s['functions']} | {s['classes']} | {s['test_files']} | {s['vectors']} | {dec_str} |")

    lines.extend([
        "",
        "## Notes",
        "",
        "- **lever-runner**: Python repo — full AST parsing with function extraction, call graph, and test detection.",
        "- **pincherOS**: Rust repo — Python AST parsing is limited; only Python files (if any) get full analysis. File structure is still captured.",
        "- **intelligent-terminal**: C++/Rust mix — similar to pincherOS, AST is limited to any Python files. File structure captured.",
        "",
        "## Methodology",
        "",
        "1. **Ingest**: Walk repo, parse Python AST, extract functions/classes/signatures/call-graph",
        "2. **Vectorize**: Build dual-side vectors (input context → output behavior) for each function",
        "3. **Decide**: Run tripartite synchronizer (hardware × application × user) → hardcode/model/hybrid/cached",
        "",
    ])

    with open(path, 'w') as fp:
        fp.write('\n'.join(lines))
    print(f"Saved {path}")


if __name__ == "__main__":
    main()
