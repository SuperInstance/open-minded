# Induction Results Summary

Generated: 2026-06-03T13:12:00 (tree-sitter multi-language update)

## Overview

| Repo | Functions | Classes | Test Files | Vectors | Call Graph Edges |
|------|-----------|---------|------------|---------|------------------|
| lever-runner | 221 | 53 | 4 | 221 | 932 |
| pincherOS | 833 | 297 | 1 | 833 | 799 |
| intelligent-terminal | 11,528 | 1,186 | 3 | 11,528 | 10,224 |

## Notes

- **lever-runner**: Python repo — full AST parsing with function extraction, call graph, and test detection.
- **pincherOS**: Rust repo — tree-sitter multi-language parsing now covers all 67 Rust files + 14 Python files. Extraction improved from 113→833 functions, 38→297 classes.
- **intelligent-terminal**: C++/Rust/C mix — tree-sitter parsing covers 690 C++, 448 C, 87 Rust, 6 Python, 1 JavaScript file. Extraction improved from 26→11,528 functions, 0→1,186 classes.

## Improvement Summary

With tree-sitter multi-language parsing:
- **pincherOS**: 113→833 functions (**7.4×** improvement), 38→297 classes
- **intelligent-terminal**: 26→11,528 functions (**443×** improvement), 0→1,186 classes

## Methodology

1. **Ingest**: Walk repo, detect language per file, parse with tree-sitter (Rust, C++, C, Python, JavaScript) or Python AST fallback
2. **Vectorize**: Build dual-side vectors (input context → output behavior) for each function
3. **Decide**: Run tripartite synchronizer (hardware × application × user) → hardcode/model/hybrid/cached
4. **Call Graph**: Resolve inter-function call edges from parsed ASTs
