# Preferences and guarded file-command fixture

The m21 directory name is retained for compatibility. This fixture validates
the current UI-independent preferences and guarded local file-command code used
by the WinUI product.

It exercises disposable test-owned folders, real Hangul filenames, theme
preference persistence, invalid-name protection and no-overwrite create/rename
behavior. It must not mutate user documents or protected user configuration.

GUI coverage is provided by the current owned WinUI GUI suite. Use the
canonical tools/winui/run_checks.py orchestration.
