"""
S/4HANA Transformation Engine
ABAPプログラムASTにS/4HANA変換ルールを適用する
"""
import re
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple

from .abap_parser import (
    AbapProgram, AbapStatement, AbapStatementType,
    AbapSelectStatement, AbapFunctionCall, AbapDataDeclaration,
)
from .simplification_rules import SimplificationRules, SimplificationRule
from .vendor_modules import (
    detect_sap_module, SapModuleType, get_field_mapping,
    TABLE_MODULE_MAP,
)


@dataclass
class MigrationOptions:
    """Migration configuration options."""
    source_version: str = "ECC 6.08"
    target_version: str = "S/4HANA 2023"
    sap_modules: List[str] = field(default_factory=lambda: ["ALL"])
    encoding: str = "utf-8"
    extensions: List[str] = field(default_factory=lambda: [".abap", ".txt", ".prog"])
    modernize_syntax: bool = True
    convert_tables: bool = True
    convert_bapis: bool = True
    convert_fm: bool = True
    generate_report: bool = True
    add_comments: bool = True
    backup_originals: bool = True
    report_format: str = "Both"


@dataclass
class ChangeRecord:
    """Single change tracked during transformation."""
    file: str = ""
    line_number: int = 0
    category: str = ""          # TABLE, FUNCTION_MODULE, BAPI, SYNTAX, SQL
    sap_module: str = ""        # FI, CO, MM, SD, BP, CROSS, ABAP
    severity: str = ""          # AUTO, REVIEW, MANUAL
    old_value: str = ""
    new_value: str = ""
    rule_id: str = ""
    description: str = ""
    description_ja: str = ""


@dataclass
class TransformResult:
    """Result of transforming one ABAP program."""
    original_program: Optional[AbapProgram] = None
    transformed_lines: List[Tuple[str, int]] = field(default_factory=list)
    changes: List[ChangeRecord] = field(default_factory=list)
    auto_converted: int = 0
    needs_review: int = 0
    manual_only: int = 0

    def add_change(self, change: ChangeRecord):
        self.changes.append(change)
        if change.severity == "AUTO":
            self.auto_converted += 1
        elif change.severity == "REVIEW":
            self.needs_review += 1
        elif change.severity == "MANUAL":
            self.manual_only += 1


class S4Transformer:
    """Main transformation engine applying S/4HANA migration rules."""

    def __init__(self, options: MigrationOptions):
        self.options = options
        self.rules = SimplificationRules(
            source_version=options.source_version,
            target_version=options.target_version,
        )

    def transform(self, program: AbapProgram, source_file: str = "") -> TransformResult:
        """Transform an ABAP program by applying all applicable S/4HANA rules."""
        result = TransformResult(original_program=program)

        # Detect SAP modules involved
        detected_modules = detect_sap_module(
            program.tables_used, program.function_modules_used
        )

        # Check if we should process based on module filter
        if "ALL" not in self.options.sap_modules:
            filter_set = set(self.options.sap_modules)
            detected_set = {m.value for m in detected_modules}
            if not filter_set.intersection(detected_set) and detected_set:
                # No overlap - just pass through unchanged
                for stmt in program.statements:
                    result.transformed_lines.append((stmt.raw_text, stmt.line_number))
                return result

        # Process each statement through the transformation pipeline
        for stmt in program.statements:
            transformed_text = stmt.raw_text
            line_num = stmt.line_number

            # Apply transformations in order
            if self.options.convert_tables:
                transformed_text = self._transform_table_access(
                    transformed_text, line_num, stmt, source_file, result
                )

            if self.options.convert_fm:
                transformed_text = self._transform_function_calls(
                    transformed_text, line_num, stmt, source_file, result
                )

            if self.options.convert_bapis:
                transformed_text = self._transform_bapi_calls(
                    transformed_text, line_num, stmt, source_file, result
                )

            if self.options.modernize_syntax:
                transformed_text = self._transform_sql_syntax(
                    transformed_text, line_num, stmt, source_file, result
                )
                transformed_text = self._transform_obsolete_syntax(
                    transformed_text, line_num, stmt, source_file, result
                )
                transformed_text = self._transform_exec_sql(
                    transformed_text, line_num, stmt, source_file, result
                )

            result.transformed_lines.append((transformed_text, line_num))

        return result

    # ------------------------------------------------------------------ #
    #  Table Access Transformation                                        #
    # ------------------------------------------------------------------ #

    def _transform_table_access(
        self, text: str, line_num: int, stmt: AbapStatement,
        source_file: str, result: TransformResult
    ) -> str:
        """Replace deprecated table names in SELECT/INSERT/UPDATE/DELETE/MODIFY."""
        table_mappings = self.rules.table_mappings
        if not table_mappings:
            return text

        upper_text = text.upper()

        # Match table names in SQL-like contexts
        # FROM table, INTO table, UPDATE table, MODIFY table, DELETE FROM table
        patterns = [
            (r'(?i)\bFROM\s+(\w+)', 'FROM'),
            (r'(?i)\bINTO\s+(\w+)', 'INTO'),
            (r'(?i)\bUPDATE\s+(\w+)', 'UPDATE'),
            (r'(?i)\bMODIFY\s+(\w+)', 'MODIFY'),
            (r'(?i)\bDELETE\s+FROM\s+(\w+)', 'DELETE'),
            (r'(?i)\bJOIN\s+(\w+)', 'JOIN'),
        ]

        for pattern, ctx in patterns:
            for match in re.finditer(pattern, text):
                table_name = match.group(1).upper()
                if table_name in table_mappings:
                    rule = table_mappings[table_name]
                    # Check module filter
                    if not self._module_allowed(rule.sap_module):
                        continue

                    new_table = rule.new_pattern
                    # Replace preserving case style
                    text = self._replace_identifier(
                        text, match.group(1), new_table, match.start(1), match.end(1)
                    )

                    module_str = TABLE_MODULE_MAP.get(
                        table_name, SapModuleType.CROSS
                    )
                    if isinstance(module_str, SapModuleType):
                        module_str = module_str.value

                    result.add_change(ChangeRecord(
                        file=source_file,
                        line_number=line_num,
                        category="TABLE",
                        sap_module=rule.sap_module,
                        severity=rule.severity,
                        old_value=table_name,
                        new_value=new_table,
                        rule_id=rule.rule_id,
                        description=rule.description,
                        description_ja=rule.description_ja,
                    ))

                    # If there's a field mapping, add review note
                    if rule.field_mapping:
                        field_map_str = ", ".join(
                            f"{k}→{v}" for k, v in list(rule.field_mapping.items())[:5]
                        )
                        result.add_change(ChangeRecord(
                            file=source_file,
                            line_number=line_num,
                            category="TABLE",
                            sap_module=rule.sap_module,
                            severity="REVIEW",
                            old_value=f"{table_name} fields",
                            new_value=f"Field mapping: {field_map_str}...",
                            rule_id=f"{rule.rule_id}_FIELDS",
                            description=f"Field names changed: {field_map_str}",
                            description_ja=f"フィールド名変更: {field_map_str}",
                        ))
                    break  # Only process first match per pattern

        return text

    # ------------------------------------------------------------------ #
    #  Function Module Call Transformation                                #
    # ------------------------------------------------------------------ #

    def _transform_function_calls(
        self, text: str, line_num: int, stmt: AbapStatement,
        source_file: str, result: TransformResult
    ) -> str:
        """Replace deprecated function module calls."""
        if stmt.type != AbapStatementType.CALL_FUNCTION:
            return text

        fm_mappings = self.rules.fm_mappings
        if not fm_mappings:
            return text

        # Extract FM name from CALL FUNCTION 'FM_NAME'
        fm_match = re.search(r"(?i)CALL\s+FUNCTION\s+'([^']+)'", text)
        if not fm_match:
            return text

        fm_name = fm_match.group(1).upper()
        if fm_name not in fm_mappings:
            return text

        rule = fm_mappings[fm_name]
        if not self._module_allowed(rule.sap_module):
            return text

        if rule.auto_fix and rule.severity == "AUTO":
            # Auto-replace the function module name
            text = text[:fm_match.start(1)] + rule.new_pattern + text[fm_match.end(1):]

        result.add_change(ChangeRecord(
            file=source_file,
            line_number=line_num,
            category="FUNCTION_MODULE",
            sap_module=rule.sap_module,
            severity=rule.severity,
            old_value=fm_name,
            new_value=rule.new_pattern,
            rule_id=rule.rule_id,
            description=rule.description,
            description_ja=rule.description_ja,
        ))

        return text

    # ------------------------------------------------------------------ #
    #  BAPI Call Transformation                                           #
    # ------------------------------------------------------------------ #

    def _transform_bapi_calls(
        self, text: str, line_num: int, stmt: AbapStatement,
        source_file: str, result: TransformResult
    ) -> str:
        """Replace deprecated BAPI calls."""
        if stmt.type != AbapStatementType.CALL_FUNCTION:
            return text

        bapi_mappings = self.rules.bapi_mappings
        if not bapi_mappings:
            return text

        fm_match = re.search(r"(?i)CALL\s+FUNCTION\s+'([^']+)'", text)
        if not fm_match:
            return text

        bapi_name = fm_match.group(1).upper()
        if not bapi_name.startswith("BAPI_"):
            return text

        if bapi_name not in bapi_mappings:
            return text

        rule = bapi_mappings[bapi_name]
        if not self._module_allowed(rule.sap_module):
            return text

        result.add_change(ChangeRecord(
            file=source_file,
            line_number=line_num,
            category="BAPI",
            sap_module=rule.sap_module,
            severity=rule.severity,
            old_value=bapi_name,
            new_value=rule.new_pattern,
            rule_id=rule.rule_id,
            description=rule.description,
            description_ja=rule.description_ja,
        ))

        return text

    # ------------------------------------------------------------------ #
    #  SQL Syntax Transformation                                          #
    # ------------------------------------------------------------------ #

    def _transform_sql_syntax(
        self, text: str, line_num: int, stmt: AbapStatement,
        source_file: str, result: TransformResult
    ) -> str:
        """Modernize ABAP SQL syntax."""
        if stmt.type not in (AbapStatementType.SELECT, AbapStatementType.ENDSELECT):
            return text

        original_text = text

        # Rule SQL_002: INTO CORRESPONDING FIELDS OF wa → INTO @DATA(wa)
        corr_match = re.search(
            r'(?i)\bINTO\s+CORRESPONDING\s+FIELDS\s+OF\s+(\w+)',
            text
        )
        if corr_match:
            wa_name = corr_match.group(1)
            new_into = f"INTO @DATA({wa_name})"
            text = text[:corr_match.start()] + new_into + text[corr_match.end():]

            rule = self.rules.get_rule_by_id("SQL_002")
            if rule:
                result.add_change(ChangeRecord(
                    file=source_file,
                    line_number=line_num,
                    category="SQL",
                    sap_module="ABAP",
                    severity=rule.severity,
                    old_value=corr_match.group(0),
                    new_value=new_into,
                    rule_id="SQL_002",
                    description=rule.description,
                    description_ja=rule.description_ja,
                ))

        # Rule SQL_005: SELECT...ENDSELECT loop detection
        if stmt.type == AbapStatementType.SELECT:
            select_obj = stmt.select
            if select_obj and select_obj.uses_endselect:
                rule = self.rules.get_rule_by_id("SQL_005")
                if rule:
                    result.add_change(ChangeRecord(
                        file=source_file,
                        line_number=line_num,
                        category="SQL",
                        sap_module="ABAP",
                        severity=rule.severity,
                        old_value="SELECT...ENDSELECT loop",
                        new_value="SELECT...INTO TABLE (batch read)",
                        rule_id="SQL_005",
                        description=rule.description,
                        description_ja=rule.description_ja,
                    ))

        return text

    # ------------------------------------------------------------------ #
    #  Obsolete ABAP Syntax Transformation                                #
    # ------------------------------------------------------------------ #

    def _transform_obsolete_syntax(
        self, text: str, line_num: int, stmt: AbapStatement,
        source_file: str, result: TransformResult
    ) -> str:
        """Convert obsolete ABAP statements to modern syntax."""
        original_text = text

        # SYNTAX_001: MOVE x TO y → y = x
        if stmt.type == AbapStatementType.MOVE:
            move_match = re.match(r'(?i)^\s*MOVE\s+(.+?)\s+TO\s+(\S+)\s*\.\s*$', text)
            if move_match:
                src_val = move_match.group(1).strip()
                dst_val = move_match.group(2).strip()
                indent = len(text) - len(text.lstrip())
                text = " " * indent + f"{dst_val} = {src_val}."
                self._record_syntax_change(
                    result, source_file, line_num, "SYNTAX_001",
                    original_text.strip(), text.strip()
                )

        # SYNTAX_002: COMPUTE y = expr → y = expr
        elif stmt.type == AbapStatementType.COMPUTE:
            compute_match = re.match(r'(?i)^\s*COMPUTE\s+(.+)$', text)
            if compute_match:
                indent = len(text) - len(text.lstrip())
                text = " " * indent + compute_match.group(1)
                self._record_syntax_change(
                    result, source_file, line_num, "SYNTAX_002",
                    original_text.strip(), text.strip()
                )

        # SYNTAX_003: ADD x TO y → y = y + x
        elif stmt.type == AbapStatementType.ADD:
            add_match = re.match(r'(?i)^\s*ADD\s+(.+?)\s+TO\s+(\S+)\s*\.\s*$', text)
            if add_match:
                val = add_match.group(1).strip()
                target = add_match.group(2).strip()
                indent = len(text) - len(text.lstrip())
                text = " " * indent + f"{target} = {target} + {val}."
                self._record_syntax_change(
                    result, source_file, line_num, "SYNTAX_003",
                    original_text.strip(), text.strip()
                )

        # SYNTAX_004: SUBTRACT x FROM y → y = y - x
        elif stmt.type == AbapStatementType.SUBTRACT:
            sub_match = re.match(r'(?i)^\s*SUBTRACT\s+(.+?)\s+FROM\s+(\S+)\s*\.\s*$', text)
            if sub_match:
                val = sub_match.group(1).strip()
                target = sub_match.group(2).strip()
                indent = len(text) - len(text.lstrip())
                text = " " * indent + f"{target} = {target} - {val}."
                self._record_syntax_change(
                    result, source_file, line_num, "SYNTAX_004",
                    original_text.strip(), text.strip()
                )

        # SYNTAX_005: MULTIPLY y BY x → y = y * x
        elif stmt.type == AbapStatementType.MULTIPLY:
            mul_match = re.match(r'(?i)^\s*MULTIPLY\s+(\S+)\s+BY\s+(.+?)\s*\.\s*$', text)
            if mul_match:
                target = mul_match.group(1).strip()
                val = mul_match.group(2).strip()
                indent = len(text) - len(text.lstrip())
                text = " " * indent + f"{target} = {target} * {val}."
                self._record_syntax_change(
                    result, source_file, line_num, "SYNTAX_005",
                    original_text.strip(), text.strip()
                )

        # SYNTAX_006: DIVIDE y BY x → y = y / x
        elif stmt.type == AbapStatementType.DIVIDE:
            div_match = re.match(r'(?i)^\s*DIVIDE\s+(\S+)\s+BY\s+(.+?)\s*\.\s*$', text)
            if div_match:
                target = div_match.group(1).strip()
                val = div_match.group(2).strip()
                indent = len(text) - len(text.lstrip())
                text = " " * indent + f"{target} = {target} / {val}."
                self._record_syntax_change(
                    result, source_file, line_num, "SYNTAX_006",
                    original_text.strip(), text.strip()
                )

        # SYNTAX_007: TABLES declaration
        elif stmt.type == AbapStatementType.TABLES:
            tables_match = re.match(r'(?i)^\s*TABLES[:\s]+(\w+)\s*\.\s*$', text)
            if tables_match:
                table_name = tables_match.group(1)
                indent = len(text) - len(text.lstrip())
                text = " " * indent + f"DATA {table_name} TYPE {table_name}."
                self._record_syntax_change(
                    result, source_file, line_num, "SYNTAX_007",
                    original_text.strip(), text.strip()
                )

        # SYNTAX_008: RANGES declaration
        elif stmt.type == AbapStatementType.RANGES:
            ranges_match = re.match(
                r'(?i)^\s*RANGES[:\s]+(\w+)\s+FOR\s+(\S+)\s*\.\s*$', text
            )
            if ranges_match:
                range_name = ranges_match.group(1)
                field_ref = ranges_match.group(2)
                indent = len(text) - len(text.lstrip())
                text = " " * indent + f"DATA {range_name} TYPE RANGE OF {field_ref}."
                self._record_syntax_change(
                    result, source_file, line_num, "SYNTAX_008",
                    original_text.strip(), text.strip()
                )

        return text

    # ------------------------------------------------------------------ #
    #  EXEC SQL Transformation                                            #
    # ------------------------------------------------------------------ #

    def _transform_exec_sql(
        self, text: str, line_num: int, stmt: AbapStatement,
        source_file: str, result: TransformResult
    ) -> str:
        """Flag EXEC SQL blocks for manual conversion."""
        if stmt.type == AbapStatementType.EXEC_SQL:
            rule = self.rules.get_rule_by_id("SQL_001")
            if rule:
                result.add_change(ChangeRecord(
                    file=source_file,
                    line_number=line_num,
                    category="SQL",
                    sap_module="ABAP",
                    severity="MANUAL",
                    old_value="EXEC SQL...ENDEXEC",
                    new_value="Convert to Open SQL / ABAP SQL",
                    rule_id="SQL_001",
                    description=rule.description,
                    description_ja=rule.description_ja,
                ))
        return text

    # ------------------------------------------------------------------ #
    #  Helper methods                                                     #
    # ------------------------------------------------------------------ #

    def _module_allowed(self, rule_module: str) -> bool:
        """Check if a rule's SAP module is included in the filter."""
        if "ALL" in self.options.sap_modules:
            return True
        # Map rule module to filter options
        module_map = {
            "FI": "FI/CO", "CO": "FI/CO",
            "MM": "MM", "SD": "SD",
            "BP": "BP", "ABAP": "ABAP Language",
            "CROSS": "ALL",  # Cross-module always included
        }
        mapped = module_map.get(rule_module, rule_module)
        if mapped == "ALL":
            return True
        return mapped in self.options.sap_modules

    def _replace_identifier(
        self, text: str, old_id: str, new_id: str,
        start: int, end: int
    ) -> str:
        """Replace an identifier at a specific position in text."""
        return text[:start] + new_id + text[end:]

    def _record_syntax_change(
        self, result: TransformResult, source_file: str,
        line_num: int, rule_id: str, old_val: str, new_val: str
    ):
        """Record a syntax modernization change."""
        rule = self.rules.get_rule_by_id(rule_id)
        if rule:
            result.add_change(ChangeRecord(
                file=source_file,
                line_number=line_num,
                category="SYNTAX",
                sap_module="ABAP",
                severity=rule.severity,
                old_value=old_val,
                new_value=new_val,
                rule_id=rule_id,
                description=rule.description,
                description_ja=rule.description_ja,
            ))
