# flyExplorer Windows validation evidence

This branch stores **bounded, non-secret evidence** from the repository-scoped
`Remote Windows Task`. It is deliberately separate from product `main`
and request-control `control/remote-shell`.

Each `runs/<run-id>/` directory contains structured result metadata and
allowlisted PASS/FAIL markers. Raw PowerShell transcripts, arbitrary command
output, access tokens, personal profile data, installers, runtime binaries and
unreviewed desktop screenshots are **not** committed. The original GitHub
Actions run remains the authoritative source of full console logs.

The first record, `37912684233`, was reconstructed from that run's existing
GitHub job log after quota failure. It **does not** claim that the missing
artifact ZIP or screenshot was recovered. Subsequent records are written by
the same job that executes validation.
