---
title: "ABAP2S4HANA - SAP S/4HANA 移行支援ツール を作った — ローカル完結で動かす実用ツール"
emoji: "🛠️"
type: "tech"
topics: ["python", "個人開発", "oss"]
published: false
---

> 本記事は Zenn 用の下書きです。Qiita に出す場合は先頭の frontmatter を削除してください。

## TL;DR

A dual-mode (GUI and CLI) Python application for SAP ECC ABAP modernization assessment and S/4HANA migration support.

- リポジトリ: https://github.com/highdefinitionaudiodriver/ABAP2S4HANA
- ライセンス: MIT / バージョン: v0.1.0

## 作った背景・課題

（なぜ作ったか。既存ツールの不満、手作業の手間などを 2〜3 段落で。）

## できること

- Dual-Mode Interface: Provides a user-friendly Tkinter GUI as well as a headless CLI mode for automated workflows.
- Syntax Modernization: Updates older ABAP syntax toward modern S/4HANA standards.
- Comprehensive Conversion Support: Identifies and assists with standard table, BAPI, and Function Module (FM) migration patterns.
- Impact Analysis Reporting: Generates detailed migration and impact analysis reports in HTML and CSV formats.
- Safe Execution: Automatically creates backups of your original source files before processing.
- Multiple Languages: Internationalized interface with built-in language settings.
- Highly Configurable: Configure source/target SAP versions (e.g., ECC 6.08 to S/4HANA 2023), file encoding, ABAP extensions, and SAP module filters (FI/CO, MM, SD, etc.).

## 仕組み / 工夫した点

（設計上のポイント。ローカル完結・プライバシー配慮・依存の少なさ など。）

## 使い方

```bash
# インストール・起動例（README から転記）
```

## ハマったところ

（開発中の課題と解決。）

## おわりに

フィードバックは Issues / Star をいただけると励みになります。

リポジトリ: https://github.com/highdefinitionaudiodriver/ABAP2S4HANA
