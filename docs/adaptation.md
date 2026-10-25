# Adaptive settings

A setting Group contains a name, topology key, increasing revision, current pickups,
curve and time multipliers. Its immutable contents have a stable digest.

Manager validates the initial group against its modeled-envelope certificate.
A proposal requires a fresh nonfuture topology observation, matching topology key,
a revision newer than both active and pending revisions, and an independently
recomputed certificate.

After the configured delay, all relay settings commit atomically. A changed or stale
topology cancels the pending transaction. Active measured relay pickup freezes
commit. The feeder rebuilds its relay objects only outside pickup, so a mid-fault
setting switch does not erase accumulated travel.

The policy test supplies an explicit active-pickup stimulus. The feeder replay
derives pickup from its measured relay state; it does not use a hidden fault oracle.

## Applicability

Topology fingerprints describe bus connectivity and voltage-forming source identity.
They do not magically include every physical operating condition. The feeder uses
an explicit source-strength mode key and certifies AG, BC and ABCG load-zone faults
at two resistances for that mode.

The group is valid only for that stated envelope, load security assumptions and
network parameters. Large inverter export, new fault resistance, instrument
failure or a different line model can invalidate conclusions.

Unknown topology is reported as incompatible. Keeping the old group is not labeled
universally safe. The weak-source-static study demonstrates why a conventional
group can miss a fault after source conditions change.

A certificate digest detects changed contents. It does not authenticate a control
authority or protect against an adversary rewriting both data and digest.
