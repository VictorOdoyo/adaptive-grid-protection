# Conventions and units

Frequency-domain quantities are RMS cosine phasors:
x(t)=sqrt(2) Re{X exp(+i 2 pi f t)}.
Three-phase complex power is sum(V conj(I)); no peak-phasor factor of one half
belongs in this expression.

Sequences are ordered **zero, positive, negative**. With a=exp(i 2 pi/3), a positive
sequence is [1,a^2,a]. Network arrays use a final axis [A,B,C].
The sequence transform and its inverse are immutable cached matrices.

Voltages are phase-to-ground volts. A stated 11 kV feeder value is line-to-line RMS,
so its phase reference is 11000/sqrt(3) V. Impedances are ohms, currents amperes,
times seconds, flux linkage volt-seconds and power VA.

Network source and inverter currents are positive into a bus. Branch currents run
from Branch.start to Branch.end. A relay at the near terminal measures current
into its protected line. Differential protection uses both terminal currents
oriented into the protected zone, so healthy through current cancels in their sum.

Residual current is Ia+Ib+Ic=3I0. It is distinct from zero-sequence current I0.
The earth-distance compensation factor (Z0-Z1)/(3 Z1) multiplies residual current.

Fourier estimates use actual timestamps in exp(-i 2 pi f t). Their phase therefore
refers to one absolute cosine clock, rather than rotating with the start of each
window. Missing samples invalidate complete affected windows.

Invalid numeric placeholders remain finite and have separate boolean masks.
They do not represent measured zero current. Fully unavailable curves are labeled
unavailable; independent true-current and setting curves remain visible.
