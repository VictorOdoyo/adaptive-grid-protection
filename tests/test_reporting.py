from protectlab import reporting as m


def test_provenance_hashes_actual_requests_and_preserves_frozen_source():
    from protectlab.results import curve, make

    config = {"case": "sample", "resolution_scale": 1, "seed": 42}
    frozen = m.provenance(config)
    result = make(
        "sample",
        {"pickup_a": 100},
        {"error": 0.01},
        {"x": [1.0, 2], "y": [0.1, 0.01]},
        [curve("Error", "x", [("y", "measured")], "h (m)", "Relative error")],
    )
    frozen["git_revision"] = "original-source"
    result = m.stamp(result, config, frozen)
    assert result["provenance"]["git_revision"] == "original-source"
    assert result["provenance"]["parameters_sha256"] == m.digest({"pickup_a": 100})
    assert m.digest(config) != m.digest({**config, "resolution_scale": 2})


def _example():
    from protectlab.results import curve, make

    return make(
        "sample",
        {"frequency_hz": 50},
        {"relative_error": 0.01},
        {"x": [1.0, 2.0, 3], "y": [0.1, 0.02, 0.01], "field": [1 + 2j, 3 + 4j]},
        [curve("Convergence", "x", [("y", "measured")], "h (m)", "Relative error")],
        {"samples": [{"x_m": 1.0, "error": 0.1}, {"x_m": 2.0, "error": 0.02}]},
    )
