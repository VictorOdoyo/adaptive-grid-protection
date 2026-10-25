import runpy
from pathlib import Path


def test_custom_fault_example_checks_independent_electrical_relations():
    path = Path(__file__).resolve().parents[1] / "examples/custom_fault.py"
    result = runpy.run_path(str(path))["calculate"]()
    assert result["relative_error"] < 1e-12
    assert abs(result["power_defect_va"]) < 1e-7
