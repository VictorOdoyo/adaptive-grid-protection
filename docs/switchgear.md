# Breakers, reclosure and pilot channels

The feeder breaker latches its first trip command and opens after a mechanical
delay. A stuck-breaker flag prevents opening. The electrical state is recomputed
after opening, so measured current and relay travel respond to actual modeled
isolation rather than an imposed post-trip trace.

Breaker failure requires a trip command followed by persistent measured current.
A current threshold or observed breaker opening resets its timer. On timeout,
upstream interruption is commanded. In the supplied feeder this is 120 ms after
the failed primary command, with a 20 A current supervisor.

A separate single-pole ArcPole waits for a prospective-current zero after contact
parting. It excludes arc voltage, restrike and transient recovery voltage.
It is not embedded as a full arc solver inside the phasor feeder.

## Reclosure

Recloser models dead time, a finite number of shots and lockout after an unsuccessful
shot. An explicit external permissive is required. sync_check compares live-bus
voltage, phase angle and frequency mismatch. Dead-bus energization is not silently
authorized by the live-bus synchronism helper.

State machines reject backward clocks. Equal-time event insertion has stable order.
Topology contacts can be debounced before a setting decision.

## Communications

The simulated Channel assigns sequence numbers, delay, bounded random jitter
and independent packet loss. Payloads are copied at send and receive boundaries.
Receiver rejects wrong sender, non-increasing sequence, future and stale messages.

Permissive overreaching logic requires local forward pickup and a fresh remote
permission. Silence is not permission. No real devices or network packets are sent.

The sender field and SHA-256 records are logical simulation guards, not
cryptographic identity, authenticated IEC 61850 messaging or a cybersecurity claim.
Pilot latency is measured separately from relay integration and breaker delay.
