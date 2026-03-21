"""
ABAP Code Generator
変換済みABAPコードを出力する
"""
import os
from datetime import datetime
from typing import List, Optional

from .s4_transformer import TransformResult, MigrationOptions, ChangeRecord


class AbapCodeGenerator:
    """Generate converted ABAP source files with migration annotations."""

    def __init__(self, options: MigrationOptions):
        self.options = options

    def generate(self, result: TransformResult, output_path: str):
        """Write converted ABAP file preserving original structure."""
        lines = []

        # Add migration header comment block
        lines.append(f"*----------------------------------------------------------------------*")
        lines.append(f"* S/4HANA Migration: {self.options.source_version} → {self.options.target_version}")
        lines.append(f"* Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"* Tool: SAP ECC to S/4HANA Migration Tool v1.0")
        lines.append(f"* Auto-converted: {result.auto_converted} | "
                      f"Review needed: {result.needs_review} | "
                      f"Manual: {result.manual_only}")
        lines.append(f"*----------------------------------------------------------------------*")

        # Build a lookup of changes by line number
        changes_by_line = {}
        for change in result.changes:
            if change.line_number not in changes_by_line:
                changes_by_line[change.line_number] = []
            changes_by_line[change.line_number].append(change)

        # Output transformed lines with migration comments
        for transformed_text, line_num in result.transformed_lines:
            if self.options.add_comments and line_num in changes_by_line:
                for change in changes_by_line[line_num]:
                    lines.append(self._format_change_comment(change))

            lines.append(transformed_text)

        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)

        # Write the file
        with open(output_path, "w", encoding=self.options.encoding, errors="replace") as f:
            f.write("\n".join(lines))

    def generate_batch(
        self, results: List[tuple], input_dir: str, output_dir: str
    ):
        """Generate converted files for a batch of results.

        Args:
            results: List of (source_filepath, TransformResult) tuples
            input_dir: Original input directory
            output_dir: Output directory
        """
        os.makedirs(output_dir, exist_ok=True)

        for source_path, result in results:
            # Compute relative path to preserve directory structure
            rel_path = os.path.relpath(source_path, input_dir)
            # Change extension to indicate it's been migrated
            base, ext = os.path.splitext(rel_path)
            output_filename = f"{base}_s4{ext}"
            output_path = os.path.join(output_dir, output_filename)

            # Ensure subdirectory exists
            os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else output_dir, exist_ok=True)

            self.generate(result, output_path)

    def _format_change_comment(self, change: ChangeRecord) -> str:
        """Format a change record as an ABAP comment."""
        severity_tag = {
            "AUTO": "S4-AUTO",
            "REVIEW": "S4-REVIEW",
            "MANUAL": "S4-MANUAL",
        }.get(change.severity, "S4-INFO")

        parts = [f"* [{severity_tag}]"]

        if change.category:
            parts.append(f"[{change.category}]")

        if change.old_value and change.new_value:
            parts.append(f"{change.old_value} → {change.new_value}")
        elif change.description:
            parts.append(change.description)

        if change.severity == "MANUAL":
            parts.append("(MANUAL CONVERSION REQUIRED)")
        elif change.severity == "REVIEW":
            parts.append("(PLEASE REVIEW)")

        return " ".join(parts)


class BackupManager:
    """Manage backup of original ABAP files before conversion."""

    @staticmethod
    def backup_file(source_path: str, backup_dir: str) -> str:
        """Create a backup copy of the original file.

        Returns the backup file path.
        """
        os.makedirs(backup_dir, exist_ok=True)
        filename = os.path.basename(source_path)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"{os.path.splitext(filename)[0]}_{timestamp}{os.path.splitext(filename)[1]}.bak"
        backup_path = os.path.join(backup_dir, backup_filename)

        with open(source_path, "r", encoding="utf-8", errors="replace") as src:
            content = src.read()
        with open(backup_path, "w", encoding="utf-8", errors="replace") as dst:
            dst.write(content)

        return backup_path

    @staticmethod
    def backup_batch(source_paths: List[str], input_dir: str, backup_dir: str):
        """Backup multiple files preserving directory structure."""
        os.makedirs(backup_dir, exist_ok=True)
        for path in source_paths:
            rel_path = os.path.relpath(path, input_dir)
            backup_path = os.path.join(backup_dir, rel_path + ".bak")
            os.makedirs(os.path.dirname(backup_path) if os.path.dirname(backup_path) else backup_dir, exist_ok=True)
            try:
                with open(path, "r", encoding="utf-8", errors="replace") as src:
                    content = src.read()
                with open(backup_path, "w", encoding="utf-8", errors="replace") as dst:
                    dst.write(content)
            except OSError:
                pass  # Skip files that can't be read
