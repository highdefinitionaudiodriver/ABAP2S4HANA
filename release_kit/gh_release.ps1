# GitHub Release 作成スニペット（PowerShell）。
# 事前に gh auth login 済みであること。タグ未作成なら gh が作成する。
# repo: https://github.com/highdefinitionaudiodriver/ABAP2S4HANA
$ver = 'v0.1.0'
$notes = Get-Content -Raw -Encoding UTF8 "$PSScriptRoot\RELEASE_NOTES.md"
gh release create $ver `
  --title "ABAP2S4HANA - SAP S/4HANA 移行支援ツール $ver" `
  --notes "$notes" `
  # 配布物を添付する場合は末尾にファイルパスを列挙: release_kit\..\dist\*.exe
