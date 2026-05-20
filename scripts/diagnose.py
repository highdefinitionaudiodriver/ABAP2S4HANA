#!/usr/bin/env python3
"""
SAP ECC → S/4HANA 移行 事前診断スクリプト（2027 年問題対応）

既存の ABAP2S4HANA 変換パイプラインに依存しない単独スクリプト。
入力ディレクトリの ABAP ソース（.abap / .txt / SE38 エクスポート）を走査し：

  - 各ファイルを AUTO / REVIEW / MANUAL に分類
  - S/4HANA 非互換 API ランキング Top 10
  - 概算工数（時間／人日）
  - HTML サマリ（A4 1〜2 枚で印刷可）

「2027 年に SAP ECC 保守が切れる前に、自社カスタム ABAP は S/4HANA でどれくらい
動くのか？」を経営層・IT 委員会に出すための初期見積もり材料。

使い方:
    python scripts/diagnose.py <abap_source_dir>            # report.csv
    python scripts/diagnose.py <abap_source_dir> --html r.html
"""

from __future__ import annotations

import argparse
import csv
import html
import re
import sys
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

# ──────────────────────────────────────────────────────────────────────────
# 判定ルール
#
# AUTO: そのまま S/4HANA でも動く（または微修正）
# REVIEW: ATC (ABAP Test Cockpit) で警告レベル。書換要・テスト要
# MANUAL: 完全に非互換。設計変更・代替実装が必要
# ──────────────────────────────────────────────────────────────────────────

AUTO_PATTERNS = [
    (r"\bDATA\s*:\s*\w+", 1, "DATA 宣言 → 互換あり"),
    (r"\bLOOP\s+AT\b", 1, "LOOP AT → 互換あり"),
    (r"\bREAD\s+TABLE\b", 1, "READ TABLE → 互換あり"),
    (r"\bIF\s+.+\.", 1, "IF 文 → 互換あり"),
    (r"\bCASE\s+\w+\.", 1, "CASE 文 → 互換あり"),
    (r"\bCALL\s+FUNCTION\b", 1, "CALL FUNCTION → ほぼ互換（BAPI は別途確認）"),
    (r"\bWRITE\s*:?\s+", 1, "WRITE (リスト出力) → 互換（ALV 推奨）"),
    (r"\bMOVE\s+\w+\s+TO\s+\w+", 1, "MOVE 構文 → 互換あり"),
    (r"\bMOVE-CORRESPONDING\b", 1, "MOVE-CORRESPONDING → 互換あり"),
    (r"\bAPPEND\s+\w+\s+TO\b", 1, "APPEND TO 内部テーブル → 互換あり"),
]

REVIEW_PATTERNS = [
    (r"\bSELECT\s+\*\s+FROM\b", 3, "SELECT * → ATC 警告。明示カラム必要"),
    (r"\bSELECT\s+SINGLE\s+\*\s+FROM\b", 2, "SELECT SINGLE * → ATC 警告"),
    (r"\b(MKPF|MSEG|BSEG|BKPF|EKKO|EKPO|VBAK|VBAP)\b", 4,
     "ECC 互換テーブル → S/4HANA では CDS View 経由を推奨"),
    (r"\b(MARA|MARC|MARD|MBEW)\b", 3,
     "古い物流テーブル → 簡素化対象。直接 SELECT は要レビュー"),
    (r"\bSY-MANDT\b", 2, "SY-MANDT 直接参照 → 暗黙クライアント処理に変更を検討"),
    (r"\bAT\s+SELECTION-SCREEN\b", 2,
     "古い SELECTION-SCREEN → SAP GUI / Fiori 両対応を検討"),
    (r"\bPERFORM\s+\w+", 3, "PERFORM (古典サブルーチン) → メソッド化推奨"),
    (r"\bFORM\s+\w+", 3, "FORM 定義 → CLASS / METHOD への置換推奨"),
    (r"\bTABLES\s*:\s*\w+", 3,
     "TABLES 宣言 (作業領域) → DATA + 構造体への書換要"),
    (r"\bRANGES\b", 2, "RANGES 構文 → 互換だが TYPE TABLE OF 推奨"),
    (r"\bOCCURS\s+\d+", 3,
     "OCCURS 句 → TYPE STANDARD TABLE OF への書換要（廃止予定）"),
    (r"\bWITH\s+HEADER\s+LINE\b", 4,
     "WITH HEADER LINE → 廃止構文。ワークエリア分離が必要"),
    (r"\bASSIGN\s+.+\s+TO\s+<\w+>", 2,
     "ASSIGN (フィールドシンボル) → 互換だが型チェック強化に注意"),
]

MANUAL_PATTERNS = [
    (r"\bCLIENT\s+SPECIFIED\b", 5,
     "CLIENT SPECIFIED → S/4HANA で大幅制限。設計変更必要"),
    (r"\bNATIVE\s+SQL\b|\bEXEC\s+SQL\b", 6,
     "NATIVE SQL / EXEC SQL → HANA SQL Script / AMDP への完全書換"),
    (r"\bCDS\s+VIEW\b", 0,
     "CDS View（既に S/4HANA 寄せ） → そのまま流用可"),
    (r"\bSUBMIT\s+\w+\s+(VIA|AND\s+RETURN)", 4,
     "SUBMIT (バッチ呼出) → SAP Job Scheduling / BTP に再設計"),
    (r"\bCALL\s+SCREEN\b", 5,
     "Dynpro (CALL SCREEN) → Fiori / SAP GUI for HTML へ移行検討"),
    (r"\bCALL\s+TRANSACTION\s+'(\w+)'", 5,
     "CALL TRANSACTION → S/4HANA で簡素化されたトランザクションを確認"),
    (r"\bBDC_OKCODE\b|\bBDCDATA\b", 6,
     "BDC バッチ入力 → BAPI / OData サービスへの再実装"),
    (r"\bSAP-LUW\b|\bSET\s+UPDATE\s+TASK\b", 5,
     "更新タスク / SAP-LUW → S/4HANA Cloud では制限あり、要検証"),
    (r"\bMODULE\s+POOL\b", 6,
     "Module Pool → ABAP RAP / Fiori への完全再設計"),
    (r"\bREUSE_ALV_GRID_DISPLAY\b|\bREUSE_ALV_LIST_DISPLAY\b", 4,
     "REUSE_ALV_* → CL_SALV_TABLE / Fiori UI への移行推奨"),
    (r"\bLDB\b|\bLOGICAL\s+DATABASE\b", 6,
     "Logical Database → 廃止。CDS View ベースに再設計"),
    (r"\bMACRO\b|\bDEFINE\s+\w+\.", 3,
     "MACRO 定義 → メソッド化、または ABAP Cloud 非互換のため再設計"),
    (r"\bFIELD-SYMBOLS\s+<\w+>\s+TYPE\s+STANDARD\s+TABLE", 2,
     "古い FIELD-SYMBOLS → 型推論強化で問題化することあり"),
    # 主要 obsolete API
    (r"\bMATNR\s+TYPE\s+MARA-MATNR\b", 2,
     "MATNR 旧長さ → S/4HANA で 40 桁拡張対応必要"),
    (r"\bVKORG\s+TYPE\s+T001W\b", 3, "古い販売組織テーブル参照 → 要見直し"),
]


@dataclass
class FileDiagnostic:
    path: str
    relative_path: str
    loc: int
    auto_hits: int = 0
    review_hits: int = 0
    manual_hits: int = 0
    weighted_effort_min: float = 0.0
    category: str = "AUTO"
    top_findings: list[tuple[str, int]] = field(default_factory=list)


def strip_comments(src: str) -> str:
    """ABAP のコメント (* で始まる行 / 行末 ") を除去。文字列内のクォートはスキップ。"""
    out: list[str] = []
    for line in src.splitlines(keepends=True):
        stripped = line.lstrip()
        if stripped.startswith("*"):
            # 行頭 * 始まりは丸ごとコメント
            out.append("\n")
            continue
        # 行末コメント " ... を取り除き（文字列リテラルを考慮）
        i, n = 0, len(line)
        in_str = False
        for i in range(n):
            ch = line[i]
            if not in_str:
                if ch == "'":
                    in_str = True
                elif ch == '"':
                    # 行末コメント開始
                    out.append(line[:i])
                    out.append("\n")
                    break
            else:
                if ch == "'":
                    in_str = False
        else:
            out.append(line)
    return "".join(out)


def read_text(path: Path) -> str:
    for enc in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            return path.read_text(encoding=enc)
        except UnicodeDecodeError:
            continue
    return path.read_text(encoding="latin-1", errors="replace")


def diagnose_file(path: Path, root: Path) -> FileDiagnostic:
    raw = read_text(path)
    code = strip_comments(raw)
    loc = code.count("\n") + 1
    findings: Counter[str] = Counter()
    effort = 0.0
    auto_hits = review_hits = manual_hits = 0
    for regex, w, desc in AUTO_PATTERNS:
        n = len(re.findall(regex, code, re.IGNORECASE))
        if n:
            auto_hits += n
            effort += n * w
            findings[desc] += n
    for regex, w, desc in REVIEW_PATTERNS:
        n = len(re.findall(regex, code, re.IGNORECASE))
        if n:
            review_hits += n
            effort += n * w
            findings[desc] += n
    for regex, w, desc in MANUAL_PATTERNS:
        n = len(re.findall(regex, code, re.IGNORECASE))
        if n:
            manual_hits += n
            effort += n * w
            findings[desc] += n

    if manual_hits > 0:
        category = "MANUAL"
    elif review_hits > 0:
        category = "REVIEW"
    else:
        category = "AUTO"

    try:
        rel = str(path.relative_to(root))
    except ValueError:
        rel = str(path)

    return FileDiagnostic(
        path=str(path),
        relative_path=rel,
        loc=loc,
        auto_hits=auto_hits,
        review_hits=review_hits,
        manual_hits=manual_hits,
        weighted_effort_min=round(effort, 1),
        category=category,
        top_findings=findings.most_common(5),
    )


def collect_files(root: Path) -> list[Path]:
    """.abap / .txt を再帰的に収集（SE38 export は .txt が多い）"""
    exts = {".abap", ".ABAP", ".txt", ".TXT"}
    return sorted(p for p in root.rglob("*") if p.is_file() and p.suffix in exts)


def write_csv(diags: list[FileDiagnostic], out_path: Path) -> None:
    headers = [
        "relative_path", "loc", "category",
        "auto_hits", "review_hits", "manual_hits",
        "estimated_effort_minutes", "top_findings",
    ]
    with out_path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, lineterminator="\r\n")
        w.writerow(headers)
        for d in diags:
            top = "; ".join(f"{n}×{c}" for n, c in d.top_findings)
            w.writerow([
                d.relative_path, d.loc, d.category,
                d.auto_hits, d.review_hits, d.manual_hits,
                d.weighted_effort_min, top,
            ])


def aggregate(diags: list[FileDiagnostic]) -> dict:
    by_cat = Counter(d.category for d in diags)
    total_min = sum(d.weighted_effort_min for d in diags)
    all_findings: Counter[str] = Counter()
    for d in diags:
        for name, n in d.top_findings:
            all_findings[name] += n
    return {
        "file_count": len(diags),
        "by_category": dict(by_cat),
        "total_loc": sum(d.loc for d in diags),
        "total_effort_min": round(total_min, 1),
        "total_effort_hr": round(total_min / 60.0, 1),
        "total_effort_pd": round(total_min / 60.0 / 8.0, 1),
        "top_unsupported": all_findings.most_common(10),
    }


def write_html(diags: list[FileDiagnostic], out_path: Path) -> None:
    agg = aggregate(diags)
    by = agg["by_category"]
    auto_c = by.get("AUTO", 0)
    review_c = by.get("REVIEW", 0)
    manual_c = by.get("MANUAL", 0)
    n = max(1, agg["file_count"])

    def pct(c: int) -> str:
        return f"{c / n * 100:.1f}"

    top_rows = "".join(
        f"<tr><td>{i + 1}</td><td>{html.escape(name)}</td><td>{count}</td></tr>"
        for i, (name, count) in enumerate(agg["top_unsupported"])
    )
    detail_rows = "".join(
        f"<tr><td>{html.escape(d.relative_path)}</td>"
        f"<td>{d.loc}</td>"
        f"<td class='cat-{d.category.lower()}'><strong>{d.category}</strong></td>"
        f"<td>{d.weighted_effort_min:.0f} 分</td>"
        f"<td>{html.escape('; '.join(f'{nm}×{cn}' for nm, cn in d.top_findings))}</td></tr>"
        for d in sorted(diags, key=lambda x: x.weighted_effort_min, reverse=True)[:20]
    )

    body = f"""<!DOCTYPE html>
<html lang="ja"><head><meta charset="UTF-8"><title>SAP ECC → S/4HANA 移行 事前診断レポート</title>
<style>
  body {{ font-family: "Yu Gothic UI", "Hiragino Sans", sans-serif; max-width: 900px; margin: 20px auto; padding: 0 18px; color: #222; }}
  h1 {{ font-size: 22px; border-bottom: 3px solid #0072c6; padding-bottom: 6px; }}
  h2 {{ font-size: 16px; margin-top: 28px; color: #0072c6; }}
  .kpi {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin: 16px 0; }}
  .kpi-box {{ padding: 14px; background: #f5f5f5; border-radius: 6px; text-align: center; }}
  .kpi-box .big {{ font-size: 24px; font-weight: bold; }}
  .kpi-box .label {{ font-size: 11px; color: #666; margin-top: 2px; }}
  .cat-auto {{ color: #2e7d32; }}
  .cat-review {{ color: #ef6c00; }}
  .cat-manual {{ color: #c62828; }}
  table {{ width: 100%; border-collapse: collapse; margin-top: 8px; font-size: 13px; }}
  th, td {{ border-bottom: 1px solid #ddd; padding: 6px 8px; text-align: left; }}
  th {{ background: #fafafa; }}
  .summary-bar {{ height: 24px; display: flex; margin: 8px 0 16px; border-radius: 4px; overflow: hidden; font-size: 11px; color: #fff; text-align: center; line-height: 24px; }}
  .seg-auto {{ background: #4caf50; }}
  .seg-review {{ background: #ff9800; }}
  .seg-manual {{ background: #e53935; }}
  .alert-2027 {{ background: #fff3cd; border-left: 4px solid #ff9800; padding: 12px; margin: 16px 0; font-size: 13px; }}
  .meta {{ font-size: 11px; color: #888; margin-top: 24px; padding-top: 12px; border-top: 1px solid #eee; }}
</style></head><body>
<h1>SAP ECC → S/4HANA 移行 事前診断レポート</h1>

<div class="alert-2027">
  ⏰ <strong>2027 年問題</strong>：SAP ECC の標準保守は 2027 年末で終了予定。
  カスタム ABAP の S/4HANA 互換性確認は早期着手を推奨します。
</div>

<div class="kpi">
  <div class="kpi-box"><div class="big">{agg['file_count']}</div><div class="label">対象 ABAP ファイル数</div></div>
  <div class="kpi-box"><div class="big">{agg['total_loc']:,}</div><div class="label">合計行数（コメント除外）</div></div>
  <div class="kpi-box"><div class="big">{agg['total_effort_pd']}</div><div class="label">概算工数（人日）</div></div>
</div>

<h2>変換可否の分布</h2>
<div class="summary-bar">
  <div class="seg-auto" style="width: {pct(auto_c)}%">AUTO {auto_c}</div>
  <div class="seg-review" style="width: {pct(review_c)}%">REVIEW {review_c}</div>
  <div class="seg-manual" style="width: {pct(manual_c)}%">MANUAL {manual_c}</div>
</div>
<table>
  <thead><tr><th>カテゴリ</th><th>意味</th><th>ファイル数</th><th>構成比</th></tr></thead>
  <tbody>
    <tr><td class="cat-auto"><strong>AUTO</strong></td><td>そのまま S/4HANA でも動作。微修正のみ。</td><td>{auto_c}</td><td>{pct(auto_c)}%</td></tr>
    <tr><td class="cat-review"><strong>REVIEW</strong></td><td>ATC 警告レベル。書換 + テスト必要（SELECT *、PERFORM、TABLES 宣言 等）。</td><td>{review_c}</td><td>{pct(review_c)}%</td></tr>
    <tr><td class="cat-manual"><strong>MANUAL</strong></td><td>非互換。設計再構築必要（Dynpro / BDC / Module Pool / Native SQL / LDB 等）。</td><td>{manual_c}</td><td>{pct(manual_c)}%</td></tr>
  </tbody>
</table>

<h2>S/4HANA 非互換 API ランキング Top 10</h2>
<table>
  <thead><tr><th>#</th><th>API / 構文</th><th>検出件数</th></tr></thead>
  <tbody>{top_rows or '<tr><td colspan="3">該当なし</td></tr>'}</tbody>
</table>

<h2>工数集中ファイル Top 20</h2>
<table>
  <thead><tr><th>ファイル</th><th>LOC</th><th>カテゴリ</th><th>概算工数</th><th>主な検出</th></tr></thead>
  <tbody>{detail_rows or '<tr><td colspan="5">該当なし</td></tr>'}</tbody>
</table>

<p class="meta">
⚠️ 本レポートは <strong>静的解析による事前見積もり</strong> です。
SAP 標準の ATC (ABAP Test Cockpit) / Custom Code Migration ツールと併用してください。
最終工数は人手レビュー + 結合テストの工数を加算してください。<br>
生成: {datetime.now().isoformat(timespec='seconds')} / ABAP2S4HANA diagnose.py
</p>
</body></html>"""
    out_path.write_text(body, encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="ABAP 資産を S/4HANA 移行可能性で事前診断（2027 年問題対応）",
    )
    parser.add_argument("input_dir", help="走査対象のディレクトリ")
    parser.add_argument("-o", "--output", default="report.csv",
                        help="CSV 出力先（デフォルト: report.csv）")
    parser.add_argument("--html", default=None, help="HTML サマリ出力先（任意）")
    args = parser.parse_args(argv)

    root = Path(args.input_dir).resolve()
    if not root.is_dir():
        print(f"エラー: ディレクトリではありません: {root}", file=sys.stderr)
        return 2

    files = collect_files(root)
    if not files:
        print(f"対象ファイル (.abap/.txt) が見つかりません: {root}", file=sys.stderr)
        return 1

    print(f"走査中: {len(files)} ファイル...", file=sys.stderr)
    diags = [diagnose_file(p, root) for p in files]

    out_csv = Path(args.output).resolve()
    write_csv(diags, out_csv)
    print(f"[OK] CSV: {out_csv}", file=sys.stderr)

    if args.html:
        out_html = Path(args.html).resolve()
        write_html(diags, out_html)
        print(f"[OK] HTML: {out_html}", file=sys.stderr)

    agg = aggregate(diags)
    by = agg["by_category"]
    print("\n=== 集計 ===", file=sys.stderr)
    print(f"  AUTO   : {by.get('AUTO', 0)} ファイル", file=sys.stderr)
    print(f"  REVIEW : {by.get('REVIEW', 0)} ファイル", file=sys.stderr)
    print(f"  MANUAL : {by.get('MANUAL', 0)} ファイル", file=sys.stderr)
    print(f"  概算工数: {agg['total_effort_hr']} 時間 (≒ {agg['total_effort_pd']} 人日)",
          file=sys.stderr)
    print("\n  非互換 API Top 5:", file=sys.stderr)
    for name, count in agg["top_unsupported"][:5]:
        print(f"    - {name}: {count}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
