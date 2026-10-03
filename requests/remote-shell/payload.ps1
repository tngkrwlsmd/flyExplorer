$ErrorActionPreference = "Stop"
$dirty = @(git status --porcelain)
if ($dirty.Count -eq 0) {
    throw "Expected Known Folder artwork development changes."
}
Write-Output "KNOWN_FOLDER_VALIDATION_STATE"
$dirty | ForEach-Object { Write-Output $_ }

git diff --check
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

python -X utf8 -m unittest tests.winui.test_known_folder_artwork_contract tests.winui.test_registered_file_type_contract tests.winui.test_file_detail_controller_contract tests.winui.test_m26_fluent_contract
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

.\test.bat source
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

.\build.bat Release
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Output "KNOWN_FOLDER_ARTWORK_BUILD_PASS"
git diff --stat
git status --short
