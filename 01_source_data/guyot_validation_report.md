# Guyot Reconstruction — Validation Report

_Generated: 2026-08-10 11:09_
_Coordinate provenance: **DIGITISED**_

Method: genuine Guyot (2012) IPD reconstruction via `IPDfromKM` from digitised
de Bono 2010 Lancet KM curves (Fig 2A OS, Fig 3 PFS), CbzP arm.
Core gates assess the CbzP reconstruction itself. Compatibility diagnostics
compare it with the current real-MP derivation using the same stratified Cox
method as the TFLs; those diagnostics are non-blocking because a mixed-source
comparison is not intrinsic validation of the digitised CbzP curve.

| Classification | Gate | Value | Target | Result |
|---|---|---|---|---|
| CORE | OS median (mo) | 15.2 | 14.1-16.1 | PASS |
| CORE | PFS median (mo) | 2.7 | 2.3-3.3 | PASS |
| CORE | OS deaths | 228 | ~227 (Table 5) | PASS |
| CORE | PFS events | 358 | reconstructed (no pub. count) | PASS |
| CORE | OS curve fit max|dev| | 0.0331 | < 0.05 | PASS |
| CORE | PFS curve fit max|dev| | 0.0174 | < 0.05 | PASS |
| COMPATIBILITY | OS stratified HR vs live MP | 0.71 (0.60-0.85) | 0.60-0.80 | PASS |
| COMPATIBILITY | PFS stratified HR vs live MP | 0.87 (0.75-1.02) | 0.64-0.84 | FAIL |

**Overall: PASS WITH WARNING** — core reconstruction PASS; comparative compatibility WARNING; provenance VERIFIED-DIGITISED.

> [!WARNING]
> The live stratified PFS comparison is outside the legacy compatibility range.
> The corrected real-MP PFS endpoint uses typed RECIST/PSA/F-042 pain/death
> components and excludes exploratory bone/clinical-progression signals. The
> mixed-source comparison must not be described as reproducing the published PFS HR.

