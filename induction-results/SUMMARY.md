# Induction Results Summary

Generated: 2026-06-03T13:05:56.534881

## Overview

| Repo | Functions | Classes | Test Files | Vectors | Decisions |
|------|-----------|---------|------------|---------|-----------|
| lever-runner | 221 | 53 | 4 | 221 | hardcode:195 |
| pincherOS | 113 | 38 | 1 | 113 | hardcode:83 |
| intelligent-terminal | 26 | 0 | 1 | 26 | hardcode:25 |

## Notes

- **lever-runner**: Python repo — full AST parsing with function extraction, call graph, and test detection.
- **pincherOS**: Rust repo — Python AST parsing is limited; only Python files (if any) get full analysis. File structure is still captured.
- **intelligent-terminal**: C++/Rust mix — similar to pincherOS, AST is limited to any Python files. File structure captured.

## Methodology

1. **Ingest**: Walk repo, parse Python AST, extract functions/classes/signatures/call-graph
2. **Vectorize**: Build dual-side vectors (input context → output behavior) for each function
3. **Decide**: Run tripartite synchronizer (hardware × application × user) → hardcode/model/hybrid/cached
