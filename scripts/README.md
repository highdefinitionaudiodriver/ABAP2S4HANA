# scripts/ — 補助ツール

メイン変換パイプラインに依存せず実行できる、見積もり・診断用の補助スクリプト集。

---

## `diagnose.py` — SAP ECC → S/4HANA 移行 事前診断（2027 年問題対応）

入力ディレクトリの ABAP ソース（`.abap` / `.txt`）を走査し、変換せず以下を出力：

- 各ファイルの **AUTO / REVIEW / MANUAL** 分類
- S/4HANA 非互換 API ランキング Top 10
- 概算工数（時間／人日）
- A4 1〜2 枚の HTML サマリ（議事録・経営層提案書に貼れる）

> 💡 これは何の役に立つのか：
> 「2027 年に SAP ECC の保守が切れる前に、自社カスタム ABAP は S/4HANA で
> どれくらい動くのか？」を IT 委員会・経営層に出すための **1 ページの数字** を
> 5 分で作るための診断ツールです。

### 使い方

```bash
# CSV のみ
python scripts/diagnose.py /path/to/abap_src

# HTML サマリも生成
python scripts/diagnose.py /path/to/abap_src --html report.html

# 出力先指定
python scripts/diagnose.py /path/to/abap_src -o estimate.csv
```

出力例（stderr）：

```
走査中: 213 ファイル...
[OK] CSV: /work/estimate.csv

=== 集計 ===
  AUTO   : 87 ファイル
  REVIEW : 84 ファイル
  MANUAL : 42 ファイル
  概算工数: 312.0 時間 (≒ 39.0 人日)

  非互換 API Top 5:
    - SELECT * → ATC 警告。明示カラム必要: 156
    - ECC 互換テーブル → S/4HANA では CDS View 経由を推奨: 89
    - PERFORM (古典サブルーチン) → メソッド化推奨: 67
    - Dynpro (CALL SCREEN) → Fiori / SAP GUI for HTML へ移行検討: 24
    - BDC バッチ入力 → BAPI / OData サービスへの再実装: 18
```

### 判定軸

| カテゴリ | 含むもの | 推定工数 |
|---|---|---|
| **AUTO** | DATA / LOOP AT / READ TABLE / IF / CASE / WRITE / MOVE / APPEND | 1 分/件 |
| **REVIEW** | `SELECT *` / 古い物流テーブル直接 SELECT / TABLES 宣言 / PERFORM / OCCURS / WITH HEADER LINE | 2-4 分/件 |
| **MANUAL** | Dynpro / BDC / Module Pool / Native SQL / Logical Database / CLIENT SPECIFIED / SUBMIT | 3-6 分/件 |

ファイル単位：
- MANUAL が 1 つでもあれば **MANUAL**
- REVIEW があれば **REVIEW**
- それ以外は **AUTO**

### 出力 CSV のスキーマ

```
relative_path, loc, category,
auto_hits, review_hits, manual_hits,
estimated_effort_minutes, top_findings
```

UTF-8 BOM 付き / CRLF（Excel 文字化け回避）

### SAP 純正ツールとの違い

| 観点 | SAP 純正 (ATC / Custom Code Migration) | 本ツール |
|---|---|---|
| 必要条件 | SAP ライセンス + ECC/S/4HANA システム接続 | OSS、ABAP ソースのみあれば実行可能 |
| 精度 | ★★★★★（実 SAP 環境での解析） | ★★★（正規表現ベースの静的解析） |
| 用途 | 実プロジェクトの正本判定 | **PoC 前の概算見積もり・ベンダー比較** |
| 工数集計 | 個別に表示 | **ファイル単位の工数を 1 行で出力** |

→ 本ツールは「SAP 純正の代替」ではなく「**初期見積もりの叩き台**」として使用してください。

### 商用利用

- 個人・社内 PoC は無料（MIT）
- 自社 ABAP 資産の **診断レポート受託**（A4 PDF 納品 + 推奨移行戦略）は応相談
- 業界特化（製造・小売・金融）の追加チェックパターン開発も対応
- 連絡先: highdefinitionaudiodriver@gmail.com
