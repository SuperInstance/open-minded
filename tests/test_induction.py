"""Tests for the induction module."""

import ast
import os
import tempfile
import shutil
import pytest

# Setup: create a temp repo for testing
SAMPLE_PYTHON = '''
"""A sample module for testing."""

def add(a: int, b: int) -> int:
    """Add two numbers together."""
    return a + b

def multiply(a, b):
    """Multiply two numbers."""
    result = a * b
    return result

def complex_function(data, threshold=0.5):
    """Process data with a threshold filter."""
    filtered = filter_values(data, threshold)
    results = transform(filtered)
    return results

def filter_values(data, threshold):
    return [x for x in data if x > threshold]

def transform(data):
    return [x * 2 for x in data]

class Calculator:
    """A simple calculator class."""

    def __init__(self, precision=2):
        self.precision = precision

    def add(self, a, b):
        result = a + b
        return round(result, self.precision)

    def subtract(self, a, b):
        return round(a - b, self.precision)
'''

SAMPLE_TEST = '''
"""Tests for sample module."""
import sample_module

def test_add():
    assert sample_module.add(1, 2) == 3

def test_multiply():
    assert sample_module.multiply(2, 3) == 6

def test_calculator():
    calc = sample_module.Calculator()
    assert calc.add(1.111, 2.222) == 3.33
'''


@pytest.fixture
def temp_repo():
    """Create a temporary repo structure for testing."""
    tmpdir = tempfile.mkdtemp(prefix="open-mind-test-")

    # Create the sample module
    with open(os.path.join(tmpdir, "sample_module.py"), "w") as f:
        f.write(SAMPLE_PYTHON)

    # Create test file
    with open(os.path.join(tmpdir, "test_sample.py"), "w") as f:
        f.write(SAMPLE_TEST)

    # Create a subpackage
    os.makedirs(os.path.join(tmpdir, "subpkg"))
    with open(os.path.join(tmpdir, "subpkg", "__init__.py"), "w") as f:
        f.write("")
    with open(os.path.join(tmpdir, "subpkg", "helper.py"), "w") as f:
        f.write(
            '''
def helper_func(x):
    """A helper function."""
    return x * 2
'''
        )

    yield tmpdir
    shutil.rmtree(tmpdir, ignore_errors=True)


# ====== Ingester Tests ======

class TestIngester:
    def test_parse_python_file(self, temp_repo):
        """Test parsing a Python file extracts functions and classes."""
        from interpreter.induction.ingester import _parse_python_file

        functions, classes = _parse_python_file(
            os.path.join(temp_repo, "sample_module.py"),
            "sample_module"
        )

        func_names = [f.name for f in functions]
        assert "add" in func_names
        assert "multiply" in func_names
        assert "complex_function" in func_names
        assert "filter_values" in func_names
        assert "transform" in func_names

        class_names = [c.name for c in classes]
        assert "Calculator" in class_names

    def test_function_extraction(self, temp_repo):
        """Test that function metadata is extracted correctly."""
        from interpreter.induction.ingester import _parse_python_file

        functions, _ = _parse_python_file(
            os.path.join(temp_repo, "sample_module.py"),
            "sample_module"
        )

        add_func = next(f for f in functions if f.name == "add")
        assert add_func.docstring == "Add two numbers together."
        assert add_func.return_type == "int"
        assert "a" in add_func.arg_names
        assert "b" in add_func.arg_names

    def test_class_extraction(self, temp_repo):
        """Test that class metadata is extracted correctly."""
        from interpreter.induction.ingester import _parse_python_file

        _, classes = _parse_python_file(
            os.path.join(temp_repo, "sample_module.py"),
            "sample_module"
        )

        calc = next(c for c in classes if c.name == "Calculator")
        assert "add" in calc.methods
        assert "subtract" in calc.methods
        assert calc.docstring is not None

    def test_call_graph(self, temp_repo):
        """Test that function calls are detected."""
        from interpreter.induction.ingester import _parse_python_file

        functions, _ = _parse_python_file(
            os.path.join(temp_repo, "sample_module.py"),
            "sample_module"
        )

        complex_func = next(f for f in functions if f.name == "complex_function")
        assert "filter_values" in complex_func.calls
        assert "transform" in complex_func.calls

    def test_is_test_file(self):
        """Test test file detection heuristic."""
        from interpreter.induction.ingester import _is_test_file

        assert _is_test_file("test_sample.py")
        assert _is_test_file("sample_test.py")
        assert _is_test_file("tests/test_main.py")
        assert not _is_test_file("sample.py")
        assert not _is_test_file("main.py")

    def test_ingest_local(self, temp_repo):
        """Test full ingestion on a local directory."""
        from interpreter.induction.ingester import ingest

        result = ingest(f"file://{temp_repo}", target_dir=temp_repo)
        assert result.stats["total_functions"] >= 5
        assert result.stats["total_classes"] >= 1
        assert result.stats["test_files"] >= 1


# ====== Vector Builder Tests ======

class TestVectorBuilder:
    def test_simple_hash_embed(self):
        """Test that hash embedding produces consistent vectors."""
        from interpreter.induction.vector_builder import _simple_hash_embed

        v1 = _simple_hash_embed("hello world")
        v2 = _simple_hash_embed("hello world")
        v3 = _simple_hash_embed("different text")

        assert len(v1) == 128
        assert v1 == v2  # Deterministic
        assert v1 != v3  # Different inputs → different vectors

    def test_cosine_similarity(self):
        """Test cosine similarity computation."""
        from interpreter.induction.vector_builder import _cosine_similarity

        # Identical vectors
        assert _cosine_similarity([1, 0, 0], [1, 0, 0]) == pytest.approx(1.0)
        # Orthogonal vectors
        assert _cosine_similarity([1, 0, 0], [0, 1, 0]) == pytest.approx(0.0)
        # Opposite vectors
        assert _cosine_similarity([1, 0, 0], [-1, 0, 0]) == pytest.approx(-1.0)

    def test_build_and_search(self, temp_repo):
        """Test building vectors and searching."""
        from interpreter.induction.ingester import ingest
        from interpreter.induction.vector_builder import VectorBuilder

        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            result = ingest(f"file://{temp_repo}", target_dir=temp_repo)
            builder = VectorBuilder(db_path=db_path)
            vectors = builder.build_all(result)

            assert len(vectors) == result.stats["total_functions"]

            # Search for input context
            matches = builder.search_input("add numbers together", repo_url=f"file://{temp_repo}", top_k=3)
            assert len(matches) > 0
            # The "add" function should score highest for "add numbers"
            top_name = matches[0][0].function_name
            assert top_name in ("add", "multiply")  # Related arithmetic functions

            # Search for output behavior
            out_matches = builder.search_output("multiply", repo_url=f"file://{temp_repo}", top_k=3)
            assert len(out_matches) > 0
        finally:
            os.unlink(db_path)

    def test_dual_vector_structure(self):
        """Test DualVector dataclass."""
        from interpreter.induction.vector_builder import DualVector

        dv = DualVector(
            function_name="test",
            module="mod",
            input_vector=[0.1] * 10,
            output_vector=[0.2] * 10,
            input_text="input",
            output_text="output",
        )
        assert dv.function_name == "test"
        assert len(dv.input_vector) == 10


# ====== Synchronizer Tests ======

class TestSynchronizer:
    def test_hardcode_decision(self):
        """Test that high safety + low latency → HARDCODE."""
        from interpreter.induction.synchronizer import Synchronizer, Decision

        sync = Synchronizer()
        result = sync.decide(
            application={"latency_ms": 10, "safety": 0.95, "creativity": 0.05, "accuracy": 0.99}
        )
        assert result.decision == Decision.HARDCODE

    def test_model_decision(self):
        """Test that high creativity + GPU → MODEL."""
        from interpreter.induction.synchronizer import Synchronizer, Decision

        sync = Synchronizer()
        result = sync.decide(
            hardware={"gpu": True, "ram_gb": 32},
            application={"latency_ms": 5000, "safety": 0.1, "creativity": 0.9, "accuracy": 0.3},
            user={"creative_output": True},
        )
        assert result.decision == Decision.MODEL

    def test_cached_decision(self):
        """Test that edge + low power + high throughput favors cached."""
        from interpreter.induction.synchronizer import Synchronizer, Decision

        sync = Synchronizer()
        result = sync.decide(
            hardware={"is_edge": True, "ram_gb": 1, "battery_pct": 5},
            application={"latency_ms": 100, "safety": 0.1, "throughput_rps": 200},
            user={"power_saving": True},
        )
        # CACHED should be in the top 2 decisions (it wins for edge + power saving)
        top_two = [result.decision] + [d for d, _ in result.alternatives[:1]]
        assert Decision.CACHED in top_two

    def test_hardware_profile_detect(self):
        """Test hardware auto-detection."""
        from interpreter.induction.synchronizer import HardwareProfile

        hw = HardwareProfile.detect()
        assert hw.ram_gb > 0
        assert hw.cpu_count > 0
        assert hw.platform_name != ""

    def test_decision_has_reasoning(self):
        """Test that decisions include explanations."""
        from interpreter.induction.synchronizer import Synchronizer

        sync = Synchronizer()
        result = sync.decide()
        assert result.reasoning
        assert result.confidence > 0
        assert len(result.alternatives) > 0


# ====== Spreader Tests ======

class TestSpreader:
    def test_spreader_creation(self, temp_repo):
        """Test creating a spreader instance."""
        from interpreter.induction.spreader import Spreader

        state_dir = tempfile.mkdtemp()
        try:
            spreader = Spreader(
                f"file://{temp_repo}",
                target_dir=temp_repo,
                state_dir=state_dir,
            )
            status = spreader.status()
            assert status["repo_url"] == f"file://{temp_repo}"
            assert status["phase"] == "idle"
        finally:
            shutil.rmtree(state_dir, ignore_errors=True)

    def test_spreader_pass_1(self, temp_repo):
        """Test pass 1 (ingestion)."""
        from interpreter.induction.spreader import Spreader

        state_dir = tempfile.mkdtemp()
        try:
            spreader = Spreader(
                f"file://{temp_repo}",
                target_dir=temp_repo,
                state_dir=state_dir,
            )
            spreader._run_pass(1)
            assert spreader._ingest_result is not None
            assert spreader.state.stats.get("ingest", {}).get("functions", 0) > 0
        finally:
            shutil.rmtree(state_dir, ignore_errors=True)

    def test_spreader_full_run(self, temp_repo):
        """Test running all 5 passes."""
        from interpreter.induction.spreader import Spreader

        state_dir = tempfile.mkdtemp()
        try:
            spreader = Spreader(
                f"file://{temp_repo}",
                target_dir=temp_repo,
                state_dir=state_dir,
            )
            spreader.start(passes=5)

            status = spreader.status()
            assert status["current_pass"] == 5
            assert status["phase"] in ("complete", "monitoring")
            assert status["hot_paths"] >= 0
        finally:
            shutil.rmtree(state_dir, ignore_errors=True)

    def test_state_persistence(self, temp_repo):
        """Test that state is persisted between instances."""
        from interpreter.induction.spreader import Spreader

        state_dir = tempfile.mkdtemp()
        try:
            spreader1 = Spreader(
                f"file://{temp_repo}",
                target_dir=temp_repo,
                state_dir=state_dir,
            )
            spreader1.start(passes=3)

            # Create a new instance pointing to same state
            spreader2 = Spreader(
                f"file://{temp_repo}",
                target_dir=temp_repo,
                state_dir=state_dir,
            )
            assert spreader2.state.current_pass == 3
        finally:
            shutil.rmtree(state_dir, ignore_errors=True)
