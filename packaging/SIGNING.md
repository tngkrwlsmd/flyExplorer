# flyExplorer production signing readiness

Status: OPEN. Windows SDK signtool.exe is installed, but the current machine
has no Code Signing certificate in CurrentUser/My or LocalMachine/My.

The latest unsigned setup/lifecycle acceptance is Remote Windows Task #435
(`37306799266`) for package candidate
`00f90c30800fb66f88184211442f6eeb05a950b7`, with runtime manifest SHA-256
`40f0f12797c6731f823dd3e438b09fc575a78a54f9962c14fb572e5d70dfdcc5`.
Production signing remains unverified because the current machine has no
approved Code Signing certificate; signed payload/setup and clean-machine
Program Files/HKLM lifecycle evidence are still required. Signing changes
artifact bytes, so the final signed release still requires fresh signed-package
verification and lifecycle evidence.

Required release order:
1. Build the final current Release runtime.
2. Sign flyExplorer.exe and FlyShellIsolationHelper.exe.
3. Verify both payload signatures.
4. Run package.bat Release so signed payload files are embedded.
5. Sign flyExplorer-Setup-x64.exe.
6. Verify the setup signature and timestamp.
7. Re-run bounded lifecycle and clean-machine Program Files/HKLM smoke.

Use an approved certificate-store or hardware-backed key. Never commit PFX
files, passwords, tokens or private-key material.

Record pre-sign and post-sign SHA-256 values because Authenticode changes the
artifact bytes. Signature success does not replace install/runtime validation
or SmartScreen/reputation observation on a clean Windows machine.
