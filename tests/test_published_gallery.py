"""Check the released scientific evidence, not a second copy of solver formulas."""

import csv
import json
import re
from pathlib import Path

import pytest

from protectlab.batch import load_catalog
from protectlab.experiments import CASES, ExperimentConfig
from protectlab.reporting import verify_report

ROOT = Path(__file__).resolve().parents[1]
GALLERY = ROOT / "docs/gallery"


@pytest.fixture(scope="module")
def captured():
    return {r["name"]: r for r in load_catalog(GALLERY)}


def test_publication_has_all_default_cases_from_one_clean_revision(captured):
    publication = json.loads((GALLERY / "publication.json").read_text(encoding="utf-8"))
    assert set(captured) == set(CASES)
    assert publication["case_count"] == 27
    for case, result in captured.items():
        assert result["configuration"] == ExperimentConfig(case).to_dict()
        assert result["provenance"]["git_revision"] == publication["source_revision"]
        assert result["provenance"]["git_dirty"] is False


@pytest.mark.parametrize("case", list(CASES))
def test_published_report_integrity_and_csv_agreement(case, captured):
    assert verify_report(GALLERY / case)
    result = captured[case]
    for table, rows in result["tables"].items():
        if not rows:
            continue
        with (GALLERY / case / ("table_" + table + ".csv")).open(encoding="utf-8", newline="") as stream:
            exported = list(csv.DictReader(stream))
        expected = [{k: "" if v is None else str(v) for k, v in row.items()} for row in rows]
        assert exported == expected
    with (GALLERY / case / "summary.csv").open(encoding="utf-8", newline="") as stream:
        exported = {row["metric"]: row["value"] for row in csv.DictReader(stream)}
    assert exported == {k: "" if v is None else str(v) for k, v in result["summary"].items()}


def test_repository_documentation_links_resolve_to_delivered_files():
    paths = [ROOT / "README.md", *(ROOT / "docs").glob("*.md")]
    for path in paths:
        for link in re.findall(r"\]\(([^)]+)\)", path.read_text(encoding="utf-8")):
            if link.startswith(("https://", "http://", "#")):
                continue
            target = link.split("#", 1)[0]
            assert (path.parent / target).exists(), (path, link)


def test_published_evidence_retains_missed_sympathetic_and_adaptive_outcomes(captured):
    assert not captured["weak-source-static"]["summary"]["required_isolation"]
    assert captured["weak-source-adaptive"]["summary"]["selective"]
    assert captured["weak-source-adaptive"]["summary"]["clearing_delay_s"] < 0.5
    assert not captured["adc-clipping"]["summary"]["selective"]
    assert captured["adc-clipping"]["summary"]["primary_measurement_valid_fraction"] == 0
    assert captured["directional-challenge"]["summary"]["unnecessary_openings"] == 1
    assert captured["robust-coordination"]["summary"]["robust_settings_worst_margin_s"] >= 0.2 - 1e-9
