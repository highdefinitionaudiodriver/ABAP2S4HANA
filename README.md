# ABAP2S4HANA Migration Tool

A dual-mode (GUI and CLI) Python application for SAP ECC ABAP modernization assessment and S/4HANA migration support.

It scans ABAP assets, applies modernization rules, and generates reviewable conversion output plus impact analysis reports. The goal is to help teams identify compatibility issues, manual remediation points, and migration effort before a full S/4HANA project begins.

---

## 🎯 これは何？（30秒で）

- **誰のため**：SAP ECC を運用中で S/4HANA 移行（2027年問題）を検討している情シス／SAP 移行プロジェクトのアセスメント担当 SI ベンダー
- **何が解決される**：カスタム ABAP 資産の S/4HANA 互換性チェックを **数週間の手作業から数時間の自動レポート**に短縮。SAP 純正ツール（SCMON / Custom Code Analyzer）で漏れる現実的な工数見積もりを補完
- **なぜ既存ツールではダメか**：SAP 純正は SAP ライセンス前提。本ツールは **OSS で社内 PoC・第三者アセスメントに利用可能**で、上司に出せる移行リスク評価レポートを出力
- **使う条件**：Python 3.10+ / Windows・macOS・Linux／GUI または CLI

## 💰 想定ユースケース・価格帯

| 用途 | 形態 |
|---|---|
| 自社内 PoC・社内アセスメント | 無料（MIT） |
| ABAP カスタムコード診断レポート受託 | 応相談 |
| エンタープライズ S/4HANA 移行案件のアセスメント支援 | 個別見積もり |

---

## Business Use Cases

- ECC to S/4HANA migration pre-assessment
- ABAP custom code inventory and compatibility risk analysis
- Impact reports for project estimates and stakeholder review
- Modernization proof-of-concept generation before production remediation

## Features

- **Dual-Mode Interface**: Provides a user-friendly Tkinter GUI as well as a headless CLI mode for automated workflows.
- **Syntax Modernization**: Updates older ABAP syntax toward modern S/4HANA standards.
- **Comprehensive Conversion Support**: Identifies and assists with standard table, BAPI, and Function Module (FM) migration patterns.
- **Impact Analysis Reporting**: Generates detailed migration and impact analysis reports in HTML and CSV formats.
- **Safe Execution**: Automatically creates backups of your original source files before processing.
- **Multiple Languages**: Internationalized interface with built-in language settings.
- **Highly Configurable**: Configure source/target SAP versions (e.g., ECC 6.08 to S/4HANA 2023), file encoding, ABAP extensions, and SAP module filters (FI/CO, MM, SD, etc.).

## Installation

1. Ensure Python 3.8+ is installed.
2. Clone the repository and install any required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### GUI Mode
Simply run the application without arguments to launch the graphical user interface:
```bash
python main.py
```

### CLI Mode
Use standard arguments to execute migrations directly from the command line:
```bash
python main.py -i <input_directory> -o <output_directory> [options]
```

**Common CLI Options:**
- `-i, --input`: Input folder containing ABAP files
- `-o, --output`: Output folder for converted ABAP files
- `-e, --encoding`: Source encoding (default: `utf-8`)
- `--source-version`: Source SAP version (e.g., `ECC 6.08`)
- `--target-version`: Target S/4HANA version (e.g., `S/4HANA 2023`)
- `--module`: SAP module filter (default: `ALL`)
- `--report-format`: Output format for the migration report (`HTML`, `CSV`, or `Both`)

Use `python main.py --help` to see all available flags for toggling modernization and backups.

## Tests

Integration and conversion tests are provided. Run them using:
```bash
python test_conversion.py
```

---

## 🤝 商用利用・カスタマイズ依頼

- 個人・社内利用は無料（MIT ライセンス）
- 法人・自治体・SI 向け導入支援、カスタマイズ、診断レポート受託は応相談
- 連絡先：highdefinitionaudiodriver@gmail.com
