# WS-7 Review Note — CI Path A seal verify

**Date:** 2026-07-09  
**Workstream:** WS-7 Release Engineering  
**Product claim:** Path A  

## Deliverable

Wire `scripts/verify_release.py` into GitHub Actions.

### Changes (`.github/workflows/ci.yml`)

1. **New job** `path-a-seal-verify`  
   - checkout + Python 3.10 only  
   - `python3 scripts/verify_release.py`  
   - `bash scripts/verify_release.sh` (wrapper parity)  
   - No R, no ODA, no patient data  

2. **Full suite step** at end of `validate` job  
   - Same `verify_release.py` after evidence badge check  

3. **Triggers**  
   - push: `main`, `codex/**`  
   - pull_request: `main`  

## Local parity

```bash
python3 scripts/verify_release.py
bash scripts/verify_release.sh
```

## Honesty

CI green means **committed seals still consistent**, not “ODA re-ran on the runner.”

## Exit

WS-7 next action (wire CI) **closed**.  
