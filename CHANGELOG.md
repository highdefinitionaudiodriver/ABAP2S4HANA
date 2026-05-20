# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- README に「これは何？（30秒で）」「想定ユースケース・価格帯」セクションを追加
- SECURITY.md を追加（脆弱性報告フロー）
- 商用利用・カスタマイズ依頼の連絡先を README 末尾に明記
- **scripts/diagnose.py** — SAP ECC → S/4HANA 移行 事前診断スクリプト（2027 年問題対応）
  - .abap / .txt を走査し AUTO / REVIEW / MANUAL 分類
  - S/4HANA 非互換 API ランキング Top 10
  - 概算工数（時間／人日）
  - HTML サマリ出力（経営層・IT 委員会向け、A4 1〜2 枚）
  - SAP 純正 ATC との違い・住み分けを scripts/README.md に明記
- scripts/.gitignore で __pycache__ 除外

## [0.1.0]

### Added
- 初版リリース
