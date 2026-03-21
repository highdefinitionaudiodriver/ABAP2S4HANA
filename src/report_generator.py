"""
Impact Analysis Report Generator
HTML/CSVフォーマットで影響分析レポートを生成する
"""
import csv
import os
from collections import Counter, defaultdict
from datetime import datetime
from typing import List, Dict

from .s4_transformer import TransformResult, ChangeRecord, MigrationOptions


class ReportGenerator:
    """Generate impact analysis reports in HTML and CSV formats."""

    def __init__(self, options: MigrationOptions):
        self.options = options

    def generate(self, results: List[TransformResult], output_dir: str):
        """Generate reports based on configured format."""
        os.makedirs(output_dir, exist_ok=True)

        if self.options.report_format in ("HTML", "Both"):
            self._generate_html(results, output_dir)
        if self.options.report_format in ("CSV", "Both"):
            self._generate_csv(results, output_dir)

    # ------------------------------------------------------------------ #
    #  HTML Report                                                        #
    # ------------------------------------------------------------------ #

    def _generate_html(self, results: List[TransformResult], output_dir: str):
        """Generate comprehensive HTML impact analysis report."""
        all_changes = []
        for r in results:
            all_changes.extend(r.changes)

        total_files = len(results)
        total_auto = sum(r.auto_converted for r in results)
        total_review = sum(r.needs_review for r in results)
        total_manual = sum(r.manual_only for r in results)
        total_changes = total_auto + total_review + total_manual

        # Aggregations
        by_category = Counter(c.category for c in all_changes)
        by_module = Counter(c.sap_module for c in all_changes)
        by_severity = Counter(c.severity for c in all_changes)
        by_file = defaultdict(list)
        for c in all_changes:
            by_file[c.file].append(c)

        manual_items = [c for c in all_changes if c.severity == "MANUAL"]

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>SAP S/4HANA Migration - Impact Analysis Report</title>
<style>
{self._get_css()}
</style>
</head>
<body>

<div class="container">

<!-- Header -->
<div class="header">
    <h1>SAP ECC → S/4HANA Migration Report</h1>
    <div class="subtitle">
        Impact Analysis | {self.options.source_version} → {self.options.target_version}
        <br>Generated: {timestamp}
    </div>
</div>

<!-- Executive Summary -->
<div class="summary-grid">
    <div class="stat-card">
        <div class="stat-number">{total_files}</div>
        <div class="stat-label">Files Analyzed</div>
    </div>
    <div class="stat-card total">
        <div class="stat-number">{total_changes}</div>
        <div class="stat-label">Total Changes</div>
    </div>
    <div class="stat-card auto">
        <div class="stat-number">{total_auto}</div>
        <div class="stat-label">Auto-Converted</div>
    </div>
    <div class="stat-card review">
        <div class="stat-number">{total_review}</div>
        <div class="stat-label">Needs Review</div>
    </div>
    <div class="stat-card manual">
        <div class="stat-number">{total_manual}</div>
        <div class="stat-label">Manual Only</div>
    </div>
</div>

<!-- Changes by SAP Module -->
<div class="section">
    <h2>Changes by SAP Module</h2>
    <table class="data-table">
        <thead>
            <tr>
                <th>Module</th>
                <th>Count</th>
                <th>Distribution</th>
            </tr>
        </thead>
        <tbody>
{self._render_module_rows(by_module, total_changes)}
        </tbody>
    </table>
</div>

<!-- Changes by Category -->
<div class="section">
    <h2>Changes by Category</h2>
    <table class="data-table">
        <thead>
            <tr>
                <th>Category</th>
                <th>Count</th>
                <th>Distribution</th>
            </tr>
        </thead>
        <tbody>
{self._render_category_rows(by_category, total_changes)}
        </tbody>
    </table>
</div>

<!-- Manual Action Items -->
{self._render_manual_section(manual_items)}

<!-- Detailed File-by-File Changes -->
<div class="section">
    <h2>Detailed Changes by File</h2>
{self._render_file_details(by_file)}
</div>

<!-- Footer -->
<div class="footer">
    <p>SAP ECC to S/4HANA Migration Tool v1.0 | Report generated: {timestamp}</p>
</div>

</div>

<script>
function toggleFile(id) {{
    var el = document.getElementById(id);
    if (el.style.display === 'none') {{
        el.style.display = 'block';
    }} else {{
        el.style.display = 'none';
    }}
}}
</script>

</body>
</html>"""

        report_path = os.path.join(output_dir, "migration_report.html")
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(html)

    def _get_css(self) -> str:
        """Return embedded CSS for the HTML report."""
        return """
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    background: #f5f6fa;
    color: #2c3e50;
    line-height: 1.6;
}
.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 20px;
}
.header {
    background: linear-gradient(135deg, #0054a6 0%, #003d7a 100%);
    color: white;
    padding: 30px;
    border-radius: 8px;
    margin-bottom: 24px;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
}
.header h1 { font-size: 24px; margin-bottom: 8px; }
.subtitle { opacity: 0.9; font-size: 14px; }
.summary-grid {
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 16px;
    margin-bottom: 24px;
}
.stat-card {
    background: white;
    border-radius: 8px;
    padding: 20px;
    text-align: center;
    box-shadow: 0 2px 4px rgba(0,0,0,0.08);
    border-top: 4px solid #bdc3c7;
}
.stat-card.total { border-top-color: #3498db; }
.stat-card.auto { border-top-color: #27ae60; }
.stat-card.review { border-top-color: #f39c12; }
.stat-card.manual { border-top-color: #e74c3c; }
.stat-number { font-size: 32px; font-weight: bold; color: #2c3e50; }
.stat-label { font-size: 13px; color: #7f8c8d; margin-top: 4px; }
.section {
    background: white;
    border-radius: 8px;
    padding: 24px;
    margin-bottom: 24px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.08);
}
.section h2 {
    font-size: 18px;
    margin-bottom: 16px;
    padding-bottom: 8px;
    border-bottom: 2px solid #ecf0f1;
    color: #2c3e50;
}
.data-table {
    width: 100%;
    border-collapse: collapse;
}
.data-table th, .data-table td {
    padding: 10px 14px;
    text-align: left;
    border-bottom: 1px solid #ecf0f1;
}
.data-table th {
    background: #f8f9fa;
    font-weight: 600;
    font-size: 13px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    color: #7f8c8d;
}
.data-table tr:hover { background: #f8f9fa; }
.bar-container {
    width: 200px;
    height: 20px;
    background: #ecf0f1;
    border-radius: 10px;
    overflow: hidden;
    display: inline-block;
    vertical-align: middle;
}
.bar {
    height: 100%;
    background: #3498db;
    border-radius: 10px;
    transition: width 0.3s;
}
.badge {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 12px;
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
}
.badge-auto { background: #d5f5e3; color: #1e8449; }
.badge-review { background: #fdebd0; color: #d68910; }
.badge-manual { background: #fadbd8; color: #c0392b; }
.file-header {
    cursor: pointer;
    padding: 12px 16px;
    background: #f8f9fa;
    border: 1px solid #ecf0f1;
    border-radius: 6px;
    margin-bottom: 8px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    transition: background 0.2s;
}
.file-header:hover { background: #eef1f5; }
.file-header .filename { font-weight: 600; font-size: 14px; }
.file-header .file-stats { font-size: 13px; color: #7f8c8d; }
.file-changes {
    display: none;
    padding: 12px 16px;
    border: 1px solid #ecf0f1;
    border-top: none;
    border-radius: 0 0 6px 6px;
    margin-bottom: 16px;
    margin-top: -8px;
}
.change-item {
    padding: 8px 12px;
    border-left: 3px solid #bdc3c7;
    margin-bottom: 8px;
    font-size: 13px;
    background: #fafafa;
    border-radius: 0 4px 4px 0;
}
.change-item.auto { border-left-color: #27ae60; }
.change-item.review { border-left-color: #f39c12; }
.change-item.manual { border-left-color: #e74c3c; }
.change-line { color: #7f8c8d; font-size: 12px; }
.change-desc { margin-top: 2px; }
.change-values {
    font-family: 'Consolas', monospace;
    font-size: 12px;
    color: #555;
    margin-top: 4px;
}
.manual-section {
    background: #fff5f5;
    border: 1px solid #feb2b2;
    border-radius: 8px;
    padding: 24px;
    margin-bottom: 24px;
}
.manual-section h2 { color: #c0392b; border-bottom-color: #feb2b2; }
.manual-item {
    padding: 12px;
    background: white;
    border-radius: 6px;
    margin-bottom: 8px;
    border-left: 4px solid #e74c3c;
}
.footer {
    text-align: center;
    padding: 20px;
    color: #95a5a6;
    font-size: 12px;
}
@media (max-width: 768px) {
    .summary-grid { grid-template-columns: repeat(2, 1fr); }
    .bar-container { width: 100px; }
}
"""

    def _render_module_rows(self, by_module: Counter, total: int) -> str:
        """Render SAP module breakdown table rows."""
        module_names = {
            "FI": "FI (Financial Accounting)",
            "CO": "CO (Controlling)",
            "MM": "MM (Materials Management)",
            "SD": "SD (Sales & Distribution)",
            "BP": "BP (Business Partner)",
            "PP": "PP (Production Planning)",
            "ABAP": "ABAP Language",
            "CROSS": "Cross-Module",
        }
        rows = []
        for module, count in by_module.most_common():
            pct = (count / total * 100) if total > 0 else 0
            name = module_names.get(module, module)
            rows.append(f"""            <tr>
                <td>{name}</td>
                <td><strong>{count}</strong></td>
                <td>
                    <div class="bar-container">
                        <div class="bar" style="width: {pct:.0f}%"></div>
                    </div>
                    <span style="margin-left:8px; font-size:13px; color:#7f8c8d">{pct:.1f}%</span>
                </td>
            </tr>""")
        return "\n".join(rows)

    def _render_category_rows(self, by_category: Counter, total: int) -> str:
        """Render category breakdown table rows."""
        cat_names = {
            "TABLE": "Table Replacements",
            "FUNCTION_MODULE": "Function Module Changes",
            "BAPI": "BAPI Changes",
            "SYNTAX": "Syntax Modernization",
            "SQL": "SQL/Query Changes",
        }
        rows = []
        for cat, count in by_category.most_common():
            pct = (count / total * 100) if total > 0 else 0
            name = cat_names.get(cat, cat)
            rows.append(f"""            <tr>
                <td>{name}</td>
                <td><strong>{count}</strong></td>
                <td>
                    <div class="bar-container">
                        <div class="bar" style="width: {pct:.0f}%"></div>
                    </div>
                    <span style="margin-left:8px; font-size:13px; color:#7f8c8d">{pct:.1f}%</span>
                </td>
            </tr>""")
        return "\n".join(rows)

    def _render_manual_section(self, manual_items: List[ChangeRecord]) -> str:
        """Render manual action items section."""
        if not manual_items:
            return ""

        items_html = []
        for item in manual_items:
            items_html.append(f"""    <div class="manual-item">
        <div><strong>{item.file}</strong> (Line {item.line_number})</div>
        <div>{item.description}</div>
        <div class="change-values">{item.old_value} → {item.new_value}</div>
    </div>""")

        return f"""<div class="manual-section">
    <h2>Required Manual Actions ({len(manual_items)} items)</h2>
    <p style="margin-bottom:16px; color:#7f8c8d;">
        These items cannot be auto-converted and require manual developer intervention.
    </p>
{"".join(items_html)}
</div>"""

    def _render_file_details(self, by_file: Dict[str, List[ChangeRecord]]) -> str:
        """Render collapsible file-by-file change details."""
        blocks = []
        for idx, (filepath, changes) in enumerate(sorted(by_file.items())):
            file_id = f"file_{idx}"
            auto_count = sum(1 for c in changes if c.severity == "AUTO")
            review_count = sum(1 for c in changes if c.severity == "REVIEW")
            manual_count = sum(1 for c in changes if c.severity == "MANUAL")

            stats_parts = []
            if auto_count:
                stats_parts.append(f'<span class="badge badge-auto">{auto_count} auto</span>')
            if review_count:
                stats_parts.append(f'<span class="badge badge-review">{review_count} review</span>')
            if manual_count:
                stats_parts.append(f'<span class="badge badge-manual">{manual_count} manual</span>')
            stats_html = " ".join(stats_parts)

            display_name = os.path.basename(filepath) if filepath else "(unknown)"

            changes_html = []
            for c in sorted(changes, key=lambda x: x.line_number):
                sev_class = c.severity.lower()
                changes_html.append(f"""        <div class="change-item {sev_class}">
            <span class="badge badge-{sev_class}">{c.severity}</span>
            <span class="change-line">Line {c.line_number} | {c.category} | {c.sap_module}</span>
            <div class="change-desc">{c.description}</div>
            <div class="change-values">{_escape_html(c.old_value)} → {_escape_html(c.new_value)}</div>
        </div>""")

            blocks.append(f"""    <div class="file-header" onclick="toggleFile('{file_id}')">
        <span class="filename">{_escape_html(display_name)}</span>
        <span class="file-stats">{stats_html} | {len(changes)} changes</span>
    </div>
    <div class="file-changes" id="{file_id}">
{"".join(changes_html)}
    </div>""")

        return "\n".join(blocks)

    # ------------------------------------------------------------------ #
    #  CSV Report                                                         #
    # ------------------------------------------------------------------ #

    def _generate_csv(self, results: List[TransformResult], output_dir: str):
        """Generate CSV report with one row per change."""
        csv_path = os.path.join(output_dir, "migration_report.csv")

        all_changes = []
        for r in results:
            all_changes.extend(r.changes)

        with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow([
                "File", "Line", "Category", "SAP Module", "Severity",
                "Old Value", "New Value", "Rule ID", "Description",
                "Description (JA)",
            ])
            for c in sorted(all_changes, key=lambda x: (x.file, x.line_number)):
                writer.writerow([
                    c.file, c.line_number, c.category, c.sap_module,
                    c.severity, c.old_value, c.new_value, c.rule_id,
                    c.description, c.description_ja,
                ])

    # ------------------------------------------------------------------ #
    #  Summary report for GUI log                                         #
    # ------------------------------------------------------------------ #

    @staticmethod
    def get_summary(results: List[TransformResult]) -> Dict:
        """Get summary statistics for GUI display."""
        total_auto = sum(r.auto_converted for r in results)
        total_review = sum(r.needs_review for r in results)
        total_manual = sum(r.manual_only for r in results)

        all_changes = []
        for r in results:
            all_changes.extend(r.changes)

        return {
            "total_files": len(results),
            "total_changes": total_auto + total_review + total_manual,
            "auto_converted": total_auto,
            "needs_review": total_review,
            "manual_only": total_manual,
            "by_category": dict(Counter(c.category for c in all_changes)),
            "by_module": dict(Counter(c.sap_module for c in all_changes)),
        }


def _escape_html(text: str) -> str:
    """Escape HTML special characters."""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )
