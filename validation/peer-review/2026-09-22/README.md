# Peer-review evidence — 2026-09-22

The [review report](../../../docs/reviews/2026-09-22-python-public-readiness.md)
records seven open P2 findings and one P3 finding. This archive is a review record,
not a remediation or scientific-acceptance claim.

Reviewed examples commit: `0120e23b44e4da73e24fa1f91506efaca383fa93`.
Reviewed app commit: `5b4883c41ba46c43678d59cd42fd8180918f64dc`.

- `clean-walkthrough-check.md` and JSON record 12 independent cached notebook
  executions from a tracked-files archive, with managed imports and original
  examples file reads blocked by Python guards. The existing dependency
  environment was reused. No numerical analysis was repeated.
- `examples-tests.log`, `plot-tests.log` and `exporter-tests.log` retain the
  successful test summaries: 52 + 92 + 3 tests, plus six subtests.
- `app-existing-exporter-tests.txt` records nine existing compiled exporter
  methods invoked directly. This is not a fresh full .NET-suite result.
- `app-contract-repros.py` reproduces the two API/adapter findings using an
  explicitly supplied app checkout and its existing Release API assembly.
  Its output is retained in `app-contract-repros.txt`.
- `static-audit.json` records notebook schema/output, hash, link and tracked-file
  checks. Its missing-link entries are known issue-URL/template placeholders,
  not broken curriculum links. The PNG inventory includes figures retained in
  the notebooks; only the three figures cited by the review are duplicated here.

Machine-specific paths in the public evidence have been replaced with
`<REVIEW_CHECKOUT>`, `<REVIEW_ENV>`, `<BESTFIT_SOURCE>`, `<EXAMPLES_SOURCE>` and
`<REVIEW_ARTIFACTS>`. These archival copies are not byte-identical to raw local
logs; recorded source hashes, observed results, counts and timings are unchanged.
The probe's checkout argument replaces its original absolute path. Full test
XML, failed sandbox attempts, copied checkouts, caches and duplicate images remain
local scratch and are not part of this archive.

To repeat the read-only API probe after building the reviewed Release API and
installing its Python dependencies in your environment:

```powershell
python validation/peer-review/2026-09-22/app-contract-repros.py --bestfit-source ../RMC-BestFit
```

The probe prints the observed exceptions and exits normally. Its zero exit code
means the probe completed, not that the reviewed defects are fixed. Use a fresh
interpreter because Pythonnet loads the selected runtime into the process.
