# Conformance Run Record — Pinnacle 21 Community (ADaM)

**Date:** 2026-06-14 · **Engine:** Pinnacle 21 Community **4.1.0** (FDA rule-pack **2304.3**, ADaMIG 1.3).

## Status: SET UP IN FULL — BLOCKED at execution by vendor build-expiry

The complete P21 toolchain was provisioned end-to-end and the validation was launched with the exact
intended parameters. The run is blocked **only** by Pinnacle 21 Community's hard-coded engine
expiration, not by anything in the data, metadata, or configuration.

### What was provisioned (reusable)
| Item | Detail |
|---|---|
| Installer | P21 Community 4.1.0 `.dmg`, public CloudFront CDN (no registration) |
| Java | bundled JRE is **x86_64** (`bad CPU type`, no Rosetta) → provisioned **arm64 Java 8** (Azul Zulu `1.8.0_492`) to run the platform-independent `p21-client-1.0.8.jar` |
| CLI jar | `…/components/lib/p21-client-1.0.8.jar` |
| Engine / config | FDA rule-pack **2304.3** → `ADaM-IG 1.3 (FDA).xml` |
| Controlled Terminology | bundled CDISC ADaM CT, latest **2024-03-29** |
| Inputs | 7 real-MP ADaM `*_prod.xpt` (zero-diff ODA run, CHANGELOG 3.6.1) + `define.xml` |

### The blocker (verified)
```
ERROR CLI.3.17 :: Pinnacle 21 Community has expired due to an extended period with no internet connection.
Caused by: IqException: Installation qualification check Expiration date check failed for GLOBAL
```
Root cause — `…/components/lib/engines/engines_v4.json`:
```
"expirationDate": "2025-03-31"
```
…vs. this environment's system clock **2026-06-14**. P21 Community engines **self-expire annually**
(forcing updates); 4.1.0 (built 2024-05-31) expired **2025-03-31**, ~14 months before the
environment date, so the CLI's `ExpirationHeaderHandler` refuses to run. **No newer Community build
exists** — every later version on the CDN (4.1.1 / 4.2.0 / 4.3.0 / 5.0.0) returns HTTP 404.

### Not done (deliberately)
- **Did not** alter the system clock or patch/bypass the `ExpirationHeaderHandler` — that is
  circumventing the vendor's license enforcement, out of bounds for a compliance deliverable.

## The exact command (ready to run where the engine is valid)
```bash
JAVA8=<arm64 Java 8>/bin/java   # e.g. Azul Zulu 8
JAR="…/Pinnacle 21 Community.app/Contents/Resources/app.asar.unpacked/components/lib/p21-client-1.0.8.jar"
COMP="…/app.asar.unpacked/components"
"$JAVA8" -jar "$JAR" \
  --engine.version=2304.3 --engine.folder="$COMP/lib" \
  --standard=adam --standard.version=1.3 --filter=FDA \
  --source.adam=06_telemetry/_p21_datasets \
  --source.define=07_define_xml/define.xml \
  --cdisc.ct.adam.version=2024-03-29 \
  --report=06_telemetry/p21_out/p21_adam_report.xlsx \
  --output=06_telemetry/p21_out
```

## Legitimate paths to actually complete the ADaM conformance run
1. **Run on a host whose real clock is within the engine validity window** (≤ 2025-03-31 for 4.1.0),
   or once Certara ships a newer non-expired Community build — using the command above verbatim.
2. **Pinnacle 21 Enterprise** (licensed, server-based, no self-expiry) — the authoritative engine FDA
   itself uses; pair with the FDA Validator Rules matched to the Data Standards Catalog.
3. Triage the resulting `p21_adam_report.xlsx` (Reject → must-fix, Error → fix/justify, Warning → disposition in ADRG).
