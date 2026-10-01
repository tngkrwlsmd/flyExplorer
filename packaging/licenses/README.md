# Release distribution license inputs

This directory is tracked so the installer can reproduce the distribution
materials for the exact M2.7 Release payload.

- `GPL-3.0.txt`: full GNU GPL version 3 text from GNU/FSF.
- `PAYLOAD_PROVENANCE.md`: hash-based mapping of the 305 runtime files to
  flyExplorer-generated files or the NuGet package/version that supplied them.
- `nuget/<package>/<version>/...`: every license, NOTICE, ThirdPartyNotices,
  COPYING, or copyright-named file found in the package/version sets that
  contributed hash-matched runtime files, plus the top-level Windows App SDK
  2.5.1 package terms.

The installer also adds repository-root `LICENSE` and `CREDITS` under its
installed `licenses/` directory. These materials improve notice compliance and
provenance, but they are not by themselves a legal conclusion that public
redistribution is cleared.
