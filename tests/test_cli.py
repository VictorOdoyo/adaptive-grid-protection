import pytest

from protectlab.cli import main


def test_cli_lists_actual_protection_catalog(capsys):
    assert main(["list"]) == 0
    output = capsys.readouterr().out
    assert "weak-source-adaptive" in output and "pilot-channel-latency" in output


def test_cli_runs_a_real_inverter_current_study(tmp_path):
    from protectlab.reporting import verify_report

    assert main(["run", "--case", "inverter-current-ceilings", "--output", str(tmp_path)]) == 0
    assert verify_report(tmp_path)


def test_cli_rejects_ambiguous_json_and_scale_overrides(tmp_path):
    path = tmp_path / "request.json"
    path.write_text("{}", encoding="utf-8")
    with pytest.raises(SystemExit) as error:
        main(["run", "--config", str(path), "--scale", "2", "--output", str(tmp_path)])
    assert error.value.code == 2
