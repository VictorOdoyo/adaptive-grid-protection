# Reproducibility and evidence

Requests contain case, resolution_scale and seed. Unknown fields and boolean
integers are rejected. Resolution is an integer 1 to 3 and seeds are 32-bit
nonnegative integers. Scale preserves physical durations and dimensions while
increasing relevant sampling or sweep counts.

```json
{"case":"weak-source-adaptive","resolution_scale":1,"seed":42}
```

```bash
protectlab run --config examples/adaptive.json --output outputs/adaptive
protectlab batch --data-only --output outputs/catalog
protectlab render outputs/catalog
protectlab verify outputs/catalog
```

## Frozen calculation

Source revision, dirty status, package versions and request digest are frozen
before running a study. Physical parameters have a separate digest. Feeder evidence
includes exact certified groups, their current envelopes, CT/filter/ADC constants,
timestamps, phasors, raw waveforms, state trajectories and event times.

fields.npz contains numeric arrays plus Unicode JSON metadata. Loading disables
pickle and verifies hashes over array dtype, shape and bytes, as well as sealed
metadata. Complex phasors remain complex arrays.

CSV/JSON exports and an HTML figure report are generated from those arrays.
A manifest hashes all report files, and verification checks exported metadata
against the archive. Generated text uses LF so Git checkout preserves hashes.

## Replay

```bash
protectlab replay outputs/adaptive/fields.npz --output outputs/replayed
```

Archive replay preserves the original solver provenance. It renders stored data
without rerunning fault, relay or CT models. Renderer versions can change image
bytes while preserving source and numeric content.

Waveform CSV replay is different: it runs relay estimation/logic on imported
samples and records the new calculation plus the input digest.

Manifests and coordination certificates are unsigned. They detect inconsistent
contents but do not establish authorship, authenticity or physical validity.
The published gallery requires all 27 default requests from one clean source
revision. Its later artifact/documentation commit is expected to have a newer SHA.
