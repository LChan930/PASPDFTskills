# Wavefunction spectrum companion

`WAVECAR.restart` accompanies the corresponding WAVECAR in the updated
executable. A renamed wave file uses its actual filename plus `.restart`.
Copy both files as original bytes; do not hand-edit or fabricate this companion.

The recognized header is `PASP_WAVE_RESTART 1`. The companion records wave-file
byte count and Adler-32 binding, saved band/k counts, representation and spin,
real-space grid where applicable, cutoff, electron count, geometry/species,
actual source k points and basis, eigenvalues and EF. Energies/cutoffs are in
Hartree, geometry in Bohr, and Cartesian k points in inverse Bohr.
`SPECTRUM SOLVED` means a spectrum was calculated; it does not certify SCF
convergence, numerical accuracy or physical convergence.

A matching valid pair restores the available spectrum and permits applicable
sampled adjacent-band isolation checks in direct Chern restart, without a hidden
eigensolve. Explicit `DFT.LBERRY.NEND` is still required, with NINT defaulting to
1. Only actually loaded bands are eligible. If an adjacent excluded band is not
covered by the saved spectrum, the corresponding gap check is unavailable.

Legacy WAVECAR without the companion remains usable by the updated executable
for an explicitly selected group; energies/EF and gap certification are
unavailable from that file alone. A present corrupt, unknown-version or
mismatched companion must fail validation rather than silently falling back.
Do not delete failed metadata to bypass that check.

The binding is not a full Hamiltonian or pseudopotential fingerprint. Retain
compatible UPFs, physical settings, basis/spin and exact complete two-dimensional
Chern mesh. Sampled isolation checks do not prove a continuum gap. Offline input
audit inventories the companion but does not validate its wave-file binding
or spectrum. WAVECAR retains its existing formatted text payload. Skill
installation does not replace an older executable.

For direct full-mesh Chern restart, the updated reader accepts both existing
serial-produced and distributed/pool-produced WAVECAR layouts. Pool-produced
files can therefore be reused by this full-mesh workflow when the actual mesh,
basis and selected bands match. The reverse serial-to-distributed reader path
remains unsupported; do not infer universal layout interchangeability.

See [direct wave and density Chern workflows](../modules/pw.md#chern-calculation-after-scf).
