# flyExplorer production signing readiness

Status: OPEN. Windows SDK signtool.exe is installed, but the current machine
has no Code Signing certificate in CurrentUser/My or LocalMachine/My.

The current unsigned setup/lifecycle path is accepted through Remote Windows
Task #382 and PR #27. Production signing remains unverified because the current
machine has no approved Code Signing certificate; signed payload/setup and
clean-machine Program Files/HKLM lifecycle evidence are still required.

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
