# flyExplorer production signing readiness

Status: **OPEN**. The Windows SDK `signtool.exe` is installed, but the current
machine has no Code Signing certificate in CurrentUser/My or LocalMachine/My.
The current Release EXE and setup therefore remain unsigned.

## Required order

1. Build the final Release runtime.
2. Sign first-party payload executables before packaging:
   - `out\winui\Release\flyExplorer.exe`
   - `out\winui\Release\FlyShellIsolationHelper.exe`
3. Verify both signatures.
4. Run `package.bat Release` so the signed payload is embedded.
5. Sign `out\package\flyExplorer-Setup-x64.exe`.
6. Verify the setup signature and timestamp.
7. Re-run bounded lifecycle, then perform the clean-machine Program Files/HKLM
   smoke using the exact signed installer.

## Command shape

Prefer a certificate/private key available through the Windows certificate
store or approved hardware-backed provider. Do not commit PFX files, passwords,
tokens, or private-key material.

```bat
signtool sign /fd SHA256 /td SHA256 /tr <RFC3161_TIMESTAMP_URL> /sha1 <CERT_THUMBPRINT> <file>
signtool verify /pa /all /v <file>
```

Record pre-sign and post-sign SHA-256 values because Authenticode changes the
artifact bytes. A successful signature check is not a substitute for the
post-sign install/runtime smoke or for SmartScreen/reputation observations on a
clean Windows machine.
