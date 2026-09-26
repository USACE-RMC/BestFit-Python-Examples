# Changelog

## 0.2.0 — Unreleased

- Correct the twelve notebooks to teach visible Python/pythonnet construction,
  configuration, headless execution and fresh-result inspection and plotting.
- Preserve the same example cases/settings and extract observation-only fixtures.
- Replace cached notebook execution with independent raw-only kernel validation;
  retain earlier project/result archives solely as comparison evidence.
- Maintain plain Python notebook sources so regeneration cannot restore the old viewer workflow.
- Preserve CFA marginal uncertainty by passing both freshly fitted marginal chains;
  retain rendered PNGs in notebooks and audit original execution/output hashes without replacing them.

Earlier development work (the cached-viewer teaching design below is superseded):

- Replace the original seven notebooks and loose scripts with twelve concise
  walkthroughs drawn from the BestFit application's saved example projects.
- Preserve 22 complete project snapshots, original settings and seeds, and the
  distinction between saved results, fresh runs, and convergence diagnostics.
- Add a locked .NET 10 / RMC.Numerics 2.2.0 runtime, checked saved-result caches,
  explicit full-settings reruns, source audits, and independent notebook execution.
- Use the canonical BestFit plotting skill package. Map 45 desktop plot slots
  through 86 acceptance variants with independent geometry evidence and a gallery.
- Document B17C examples 2 and 4 using the official reference, the app GMM/EMA
  distinction, the Nile date correction, and non-comparable model-score scopes.

- Refresh against the public BestFit `db5807d` runtime and plotting utilities;
  retain original frozen numerical inputs and all unreviewed source descriptions.
- Correct the reviewed plot labels and regression bootstrap explanation, space
  dense contour labels, and match the zero-inflated mixture's desktop log range.
- Add a pinned public plotting installer with process-local Windows long-path
  handling, active-review notice, and consistent author/reviewer/citation metadata.
- Revalidate all twelve notebooks, 51 original-settings runs, and 560 saved views;
  preserve earlier evidence separately from the current publication review.

This development update does not create a release or certify scientific review.
