# flyExplorer production signing readiness

Status: OPEN. Windows SDK signtool.exe is installed, but the current machine
has no Code Signing certificate in CurrentUser/My or LocalMachine/My.

The latest unsigned setup/source-identity acceptance is Remote Windows Task
#440 (`37376305779`) for binary source revision
`bc63c8b48e466d1275cc6dcffb0c50e02d39db60`, with runtime manifest SHA-256
`61572e65c4a593e01607147596195041ce9d530e5f9fc21c9f9517f615b26c1d`.
Production signing remains unverified because the current machine has no
approved Code Signing certificate; signed payload/setup and clean-machine
Program Files/HKLM lifecycle evidence are still required. Signing changes
artifact bytes, so the final signed release must regenerate `RELEASE_IDENTITY.json`
for the signed setup and record reserved immutable tag `v1.0.0.0` before
publication.

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
