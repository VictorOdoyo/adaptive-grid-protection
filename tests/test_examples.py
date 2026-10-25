import runpy
from pathlib import Path


def test_custom_fault_example_checks_independent_electrical_relations():
    path = Path(__file__).resolve().parents[1] / "examples/custom_fault.py"
    result = runpy.run_path(str(path))["calculate"]()
    assert result["relative_error"] < 1e-12
    assert abs(result["power_defect_va"]) < 1e-7


def test_generated_waveform_example_is_explicitly_primary_unit_and_replayable():
    from protectlab.records import replay

    path = Path(__file__).resolve().parents[1] / "examples/generate_record.py"
    generate = runpy.run_path(str(path))["generate"]
    assert replay(generate())["trip_time_s"] is None
    result = replay(generate(True))
    assert 0.12 < result["trip_time_s"] < 0.4
