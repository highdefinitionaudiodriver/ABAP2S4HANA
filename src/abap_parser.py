"""
ABAP Source Code Parser
ABAPソースファイルを解析し、構造化ASTに変換する
"""
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum


class AbapStatementType(Enum):
    DATA = "DATA"
    TYPES = "TYPES"
    CONSTANTS = "CONSTANTS"
    FIELD_SYMBOLS = "FIELD-SYMBOLS"
    SELECT = "SELECT"
    ENDSELECT = "ENDSELECT"
    CALL_FUNCTION = "CALL FUNCTION"
    PERFORM = "PERFORM"
    FORM = "FORM"
    ENDFORM = "ENDFORM"
    CLASS_DEFINITION = "CLASS DEFINITION"
    CLASS_IMPLEMENTATION = "CLASS IMPLEMENTATION"
    ENDCLASS = "ENDCLASS"
    METHOD = "METHOD"
    ENDMETHOD = "ENDMETHOD"
    EXEC_SQL = "EXEC SQL"
    ENDEXEC = "ENDEXEC"
    TABLES = "TABLES"
    RANGES = "RANGES"
    MOVE = "MOVE"
    COMPUTE = "COMPUTE"
    ADD = "ADD"
    SUBTRACT = "SUBTRACT"
    MULTIPLY = "MULTIPLY"
    DIVIDE = "DIVIDE"
    IF = "IF"
    ELSE = "ELSE"
    ELSEIF = "ELSEIF"
    ENDIF = "ENDIF"
    CASE = "CASE"
    WHEN = "WHEN"
    ENDCASE = "ENDCASE"
    LOOP = "LOOP"
    ENDLOOP = "ENDLOOP"
    DO = "DO"
    ENDDO = "ENDDO"
    WHILE = "WHILE"
    ENDWHILE = "ENDWHILE"
    READ_TABLE = "READ TABLE"
    APPEND = "APPEND"
    INSERT = "INSERT"
    MODIFY = "MODIFY"
    DELETE = "DELETE"
    UPDATE = "UPDATE"
    WRITE = "WRITE"
    REPORT = "REPORT"
    PROGRAM = "PROGRAM"
    FUNCTION_POOL = "FUNCTION-POOL"
    INCLUDE = "INCLUDE"
    COMMIT = "COMMIT"
    ROLLBACK = "ROLLBACK"
    MESSAGE = "MESSAGE"
    RAISE = "RAISE"
    TRY = "TRY"
    CATCH = "CATCH"
    ENDTRY = "ENDTRY"
    OPEN = "OPEN"
    CLOSE = "CLOSE"
    READ_DATASET = "READ DATASET"
    TRANSFER = "TRANSFER"
    CONCATENATE = "CONCATENATE"
    SPLIT = "SPLIT"
    TRANSLATE = "TRANSLATE"
    CONDENSE = "CONDENSE"
    REPLACE = "REPLACE"
    SEARCH = "SEARCH"
    SET = "SET"
    GET = "GET"
    ASSIGN = "ASSIGN"
    UNASSIGN = "UNASSIGN"
    CLEAR = "CLEAR"
    REFRESH = "REFRESH"
    FREE = "FREE"
    SORT = "SORT"
    DESCRIBE = "DESCRIBE"
    CHECK = "CHECK"
    EXIT = "EXIT"
    RETURN = "RETURN"
    STOP = "STOP"
    LEAVE = "LEAVE"
    CONTINUE = "CONTINUE"
    COMMENT = "COMMENT"
    UNKNOWN = "UNKNOWN"


# Two-word keywords that must be matched before single-word fallback
_TWO_WORD_KEYWORDS = {
    ("CALL", "FUNCTION"): AbapStatementType.CALL_FUNCTION,
    ("READ", "TABLE"): AbapStatementType.READ_TABLE,
    ("READ", "DATASET"): AbapStatementType.READ_DATASET,
    ("FIELD-SYMBOLS", ""): AbapStatementType.FIELD_SYMBOLS,
    ("EXEC", "SQL"): AbapStatementType.EXEC_SQL,
    ("FUNCTION-POOL", ""): AbapStatementType.FUNCTION_POOL,
}

# Single-word keyword map
_SINGLE_WORD_KEYWORDS = {
    "DATA": AbapStatementType.DATA,
    "TYPES": AbapStatementType.TYPES,
    "CONSTANTS": AbapStatementType.CONSTANTS,
    "FIELD-SYMBOLS": AbapStatementType.FIELD_SYMBOLS,
    "SELECT": AbapStatementType.SELECT,
    "ENDSELECT": AbapStatementType.ENDSELECT,
    "PERFORM": AbapStatementType.PERFORM,
    "FORM": AbapStatementType.FORM,
    "ENDFORM": AbapStatementType.ENDFORM,
    "ENDCLASS": AbapStatementType.ENDCLASS,
    "METHOD": AbapStatementType.METHOD,
    "ENDMETHOD": AbapStatementType.ENDMETHOD,
    "ENDEXEC": AbapStatementType.ENDEXEC,
    "TABLES": AbapStatementType.TABLES,
    "RANGES": AbapStatementType.RANGES,
    "MOVE": AbapStatementType.MOVE,
    "COMPUTE": AbapStatementType.COMPUTE,
    "ADD": AbapStatementType.ADD,
    "SUBTRACT": AbapStatementType.SUBTRACT,
    "MULTIPLY": AbapStatementType.MULTIPLY,
    "DIVIDE": AbapStatementType.DIVIDE,
    "IF": AbapStatementType.IF,
    "ELSE": AbapStatementType.ELSE,
    "ELSEIF": AbapStatementType.ELSEIF,
    "ENDIF": AbapStatementType.ENDIF,
    "CASE": AbapStatementType.CASE,
    "WHEN": AbapStatementType.WHEN,
    "ENDCASE": AbapStatementType.ENDCASE,
    "LOOP": AbapStatementType.LOOP,
    "ENDLOOP": AbapStatementType.ENDLOOP,
    "DO": AbapStatementType.DO,
    "ENDDO": AbapStatementType.ENDDO,
    "WHILE": AbapStatementType.WHILE,
    "ENDWHILE": AbapStatementType.ENDWHILE,
    "APPEND": AbapStatementType.APPEND,
    "INSERT": AbapStatementType.INSERT,
    "MODIFY": AbapStatementType.MODIFY,
    "DELETE": AbapStatementType.DELETE,
    "UPDATE": AbapStatementType.UPDATE,
    "WRITE": AbapStatementType.WRITE,
    "REPORT": AbapStatementType.REPORT,
    "PROGRAM": AbapStatementType.PROGRAM,
    "FUNCTION-POOL": AbapStatementType.FUNCTION_POOL,
    "INCLUDE": AbapStatementType.INCLUDE,
    "COMMIT": AbapStatementType.COMMIT,
    "ROLLBACK": AbapStatementType.ROLLBACK,
    "MESSAGE": AbapStatementType.MESSAGE,
    "RAISE": AbapStatementType.RAISE,
    "TRY": AbapStatementType.TRY,
    "CATCH": AbapStatementType.CATCH,
    "ENDTRY": AbapStatementType.ENDTRY,
    "OPEN": AbapStatementType.OPEN,
    "CLOSE": AbapStatementType.CLOSE,
    "TRANSFER": AbapStatementType.TRANSFER,
    "CONCATENATE": AbapStatementType.CONCATENATE,
    "SPLIT": AbapStatementType.SPLIT,
    "TRANSLATE": AbapStatementType.TRANSLATE,
    "CONDENSE": AbapStatementType.CONDENSE,
    "REPLACE": AbapStatementType.REPLACE,
    "SEARCH": AbapStatementType.SEARCH,
    "SET": AbapStatementType.SET,
    "GET": AbapStatementType.GET,
    "ASSIGN": AbapStatementType.ASSIGN,
    "UNASSIGN": AbapStatementType.UNASSIGN,
    "CLEAR": AbapStatementType.CLEAR,
    "REFRESH": AbapStatementType.REFRESH,
    "FREE": AbapStatementType.FREE,
    "SORT": AbapStatementType.SORT,
    "DESCRIBE": AbapStatementType.DESCRIBE,
    "CHECK": AbapStatementType.CHECK,
    "EXIT": AbapStatementType.EXIT,
    "RETURN": AbapStatementType.RETURN,
    "STOP": AbapStatementType.STOP,
    "LEAVE": AbapStatementType.LEAVE,
    "CONTINUE": AbapStatementType.CONTINUE,
}


# ---------------------------------------------------------------------------
# AST dataclasses
# ---------------------------------------------------------------------------

@dataclass
class AbapDataDeclaration:
    name: str
    type_ref: str = ""
    like_ref: str = ""
    value: Optional[str] = None
    is_table: bool = False
    table_type: str = ""
    line_number: int = 0
    raw_text: str = ""


@dataclass
class AbapSelectStatement:
    target_fields: List[str] = field(default_factory=list)
    from_tables: List[str] = field(default_factory=list)
    where_clause: str = ""
    into_clause: str = ""
    is_single: bool = False
    uses_endselect: bool = False
    is_exec_sql: bool = False
    join_tables: List[str] = field(default_factory=list)
    line_number: int = 0
    raw_text: str = ""


@dataclass
class AbapFunctionCall:
    function_name: str
    exporting: Dict[str, str] = field(default_factory=dict)
    importing: Dict[str, str] = field(default_factory=dict)
    tables: Dict[str, str] = field(default_factory=dict)
    exceptions: Dict[str, str] = field(default_factory=dict)
    line_number: int = 0
    raw_text: str = ""
    is_bapi: bool = False


@dataclass
class AbapFormRoutine:
    name: str
    parameters: List[str] = field(default_factory=list)
    body_lines: List[str] = field(default_factory=list)
    line_number: int = 0


@dataclass
class AbapClassDefinition:
    name: str
    superclass: str = ""
    interfaces: List[str] = field(default_factory=list)
    is_local: bool = True
    line_number: int = 0


@dataclass
class AbapStatement:
    type: AbapStatementType
    raw_text: str
    line_number: int = 0
    tokens: List[str] = field(default_factory=list)
    select: Optional[AbapSelectStatement] = None
    function_call: Optional[AbapFunctionCall] = None
    data_decl: Optional[AbapDataDeclaration] = None


@dataclass
class AbapProgram:
    report_name: str = ""
    program_type: str = ""
    source_file: str = ""
    includes: List[str] = field(default_factory=list)
    data_declarations: List[AbapDataDeclaration] = field(default_factory=list)
    field_symbols: List[str] = field(default_factory=list)
    select_statements: List[AbapSelectStatement] = field(default_factory=list)
    function_calls: List[AbapFunctionCall] = field(default_factory=list)
    form_routines: List[AbapFormRoutine] = field(default_factory=list)
    class_definitions: List[AbapClassDefinition] = field(default_factory=list)
    statements: List[AbapStatement] = field(default_factory=list)
    tables_used: set = field(default_factory=set)
    function_modules_used: set = field(default_factory=set)
    bapis_used: set = field(default_factory=set)
    has_exec_sql: bool = False
    tables_declarations: List[str] = field(default_factory=list)
    ranges_declarations: List[str] = field(default_factory=list)
    comment_lines: int = 0
    total_lines: int = 0


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------

class AbapParser:
    """Parse ABAP source code into a structured AbapProgram AST."""

    def __init__(self, encoding: str = "utf-8"):
        self.encoding = encoding

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def parse_file(self, filepath: str) -> AbapProgram:
        """Parse an ABAP source file and return an AbapProgram."""
        with open(filepath, "r", encoding=self.encoding, errors="replace") as f:
            source = f.read()
        program = self.parse_string(source)
        program.source_file = filepath
        return program

    def parse_string(self, source: str) -> AbapProgram:
        """Parse ABAP source code from a string and return an AbapProgram."""
        raw_lines = source.splitlines(keepends=False)
        program = AbapProgram()
        program.total_lines = len(raw_lines)

        # Count comment lines
        for line in raw_lines:
            stripped = line.lstrip()
            if stripped.startswith("*") or stripped.startswith('"'):
                program.comment_lines += 1

        # Preprocess: remove comments, join continuations, expand chains
        stmt_tuples = self._preprocess(raw_lines)

        # Walk through all statements and build the AST
        self._build_ast(stmt_tuples, program)
        return program

    # ------------------------------------------------------------------
    # Preprocessing
    # ------------------------------------------------------------------

    def _preprocess(self, lines: List[str]) -> List[Tuple[str, int]]:
        """Remove comments, join multi-line statements on period boundaries,
        and expand chain statements.

        Returns a list of (statement_text, original_line_number) tuples.
        Each statement_text has trailing period removed but is otherwise
        preserved in original case.
        """
        # Phase 1: strip full-line comments, inline comments, blank lines.
        # Track original 1-based line numbers.
        cleaned: List[Tuple[str, int]] = []
        in_exec_sql = False

        for idx, raw_line in enumerate(lines):
            line_num = idx + 1
            stripped = raw_line.lstrip()

            # Full-line comment: '*' in column 1 of the original line
            if stripped.startswith("*"):
                continue

            # Inside EXEC SQL ... ENDEXEC we must NOT strip inline comments
            # because " is a valid SQL character.
            if in_exec_sql:
                cleaned.append((raw_line.rstrip(), line_num))
                upper = stripped.upper().rstrip(". ")
                if upper == "ENDEXEC":
                    in_exec_sql = False
                continue

            # Check for EXEC SQL start
            if re.match(r'EXEC\s+SQL', stripped, re.IGNORECASE):
                in_exec_sql = True
                cleaned.append((raw_line.rstrip(), line_num))
                # If ENDEXEC on same line (unlikely but possible)
                if re.search(r'ENDEXEC', stripped, re.IGNORECASE):
                    in_exec_sql = False
                continue

            # Remove inline comments (text after unquoted ")
            content = self._strip_inline_comment(stripped)
            if not content.strip():
                continue
            cleaned.append((content, line_num))

        # Phase 2: join lines into period-delimited statements.
        raw_statements = self._join_on_periods(cleaned)

        # Phase 3: expand chain statements (those containing ':' and ',')
        expanded: List[Tuple[str, int]] = []
        for text, lnum in raw_statements:
            chain_results = self._split_chain_statements(text, lnum)
            expanded.extend(chain_results)

        return expanded

    def _strip_inline_comment(self, line: str) -> str:
        """Remove inline comment (text starting at unquoted double-quote).

        ABAP inline comments start with " outside a string literal.
        String literals are delimited by single quotes.
        String templates are delimited by | ... | and may contain { }.
        """
        in_string = False
        in_template = False
        i = 0
        while i < len(line):
            ch = line[i]
            if in_string:
                if ch == "'":
                    # Two consecutive quotes are an escaped quote inside a string
                    if i + 1 < len(line) and line[i + 1] == "'":
                        i += 2
                        continue
                    in_string = False
            elif in_template:
                if ch == "|":
                    in_template = False
            else:
                if ch == "'":
                    in_string = True
                elif ch == "|":
                    in_template = True
                elif ch == '"':
                    # Inline comment starts here
                    return line[:i]
            i += 1
        return line

    def _join_on_periods(
        self, cleaned: List[Tuple[str, int]]
    ) -> List[Tuple[str, int]]:
        """Join cleaned lines into period-terminated statements.

        Returns list of (statement_text_without_trailing_period, first_line_number).
        """
        statements: List[Tuple[str, int]] = []
        current_text = ""
        current_line = 0

        for text, lnum in cleaned:
            if not current_text:
                current_line = lnum

            # We need to find periods that are statement terminators
            # (not inside string literals or string templates).
            segments = self._split_on_periods(text)
            for seg_idx, segment in enumerate(segments):
                if seg_idx < len(segments) - 1:
                    # This segment is terminated by a period
                    full = (current_text + " " + segment).strip() if current_text else segment.strip()
                    if full:
                        statements.append((full, current_line))
                    current_text = ""
                    current_line = 0
                else:
                    # Last segment (no trailing period) -- accumulate
                    if current_text:
                        current_text = current_text + " " + segment
                    else:
                        current_text = segment
                        current_line = lnum

        # Remaining text (unterminated -- treat as statement anyway)
        if current_text.strip():
            statements.append((current_text.strip(), current_line))

        return statements

    def _split_on_periods(self, text: str) -> List[str]:
        """Split *text* on periods that act as ABAP statement terminators.

        Periods inside string literals ('...') or string templates (|...|) are
        not terminators.  Returns a list of segments; if the original text
        ended with a terminator period the last element will be ''.
        """
        segments: List[str] = []
        current = ""
        in_string = False
        in_template = False
        i = 0
        while i < len(text):
            ch = text[i]
            if in_string:
                current += ch
                if ch == "'":
                    if i + 1 < len(text) and text[i + 1] == "'":
                        current += text[i + 1]
                        i += 2
                        continue
                    in_string = False
            elif in_template:
                current += ch
                if ch == "|":
                    in_template = False
            else:
                if ch == "'":
                    in_string = True
                    current += ch
                elif ch == "|":
                    in_template = True
                    current += ch
                elif ch == ".":
                    # Statement terminator
                    segments.append(current)
                    current = ""
                else:
                    current += ch
            i += 1
        segments.append(current)
        return segments

    def _split_chain_statements(
        self, line: str, line_num: int
    ) -> List[Tuple[str, int]]:
        """Expand ABAP chain statements.

        Example:
            DATA: lv_a TYPE i, lv_b TYPE string
        becomes:
            DATA lv_a TYPE i
            DATA lv_b TYPE string

        If there is no colon the statement is returned as-is.
        """
        # Find the colon position (outside of string literals)
        colon_pos = self._find_unquoted_char(line, ":")
        if colon_pos < 0:
            return [(line, line_num)]

        prefix = line[:colon_pos].strip()
        rest = line[colon_pos + 1:].strip()

        if not rest:
            return [(prefix, line_num)]

        # Split on commas (outside string literals)
        parts = self._split_unquoted(rest, ",")
        results: List[Tuple[str, int]] = []
        for part in parts:
            part = part.strip()
            if part:
                results.append((prefix + " " + part, line_num))

        if not results:
            results.append((prefix, line_num))
        return results

    @staticmethod
    def _find_unquoted_char(text: str, char: str) -> int:
        """Return index of first occurrence of *char* outside string literals, or -1."""
        in_string = False
        in_template = False
        i = 0
        while i < len(text):
            ch = text[i]
            if in_string:
                if ch == "'":
                    if i + 1 < len(text) and text[i + 1] == "'":
                        i += 2
                        continue
                    in_string = False
            elif in_template:
                if ch == "|":
                    in_template = False
            else:
                if ch == "'":
                    in_string = True
                elif ch == "|":
                    in_template = True
                elif ch == char:
                    return i
            i += 1
        return -1

    @staticmethod
    def _split_unquoted(text: str, sep: str) -> List[str]:
        """Split *text* on *sep* that is not inside string literals."""
        parts: List[str] = []
        current = ""
        in_string = False
        in_template = False
        i = 0
        while i < len(text):
            ch = text[i]
            if in_string:
                current += ch
                if ch == "'":
                    if i + 1 < len(text) and text[i + 1] == "'":
                        current += text[i + 1]
                        i += 2
                        continue
                    in_string = False
            elif in_template:
                current += ch
                if ch == "|":
                    in_template = False
            else:
                if ch == "'":
                    in_string = True
                    current += ch
                elif ch == "|":
                    in_template = True
                    current += ch
                elif ch == sep:
                    parts.append(current)
                    current = ""
                else:
                    current += ch
            i += 1
        parts.append(current)
        return parts

    # ------------------------------------------------------------------
    # Tokenizer
    # ------------------------------------------------------------------

    def _tokenize(self, text: str) -> List[str]:
        """Split an ABAP statement into tokens, respecting string literals
        and string templates."""
        tokens: List[str] = []
        current = ""
        in_string = False
        in_template = False
        i = 0
        while i < len(text):
            ch = text[i]
            if in_string:
                current += ch
                if ch == "'":
                    if i + 1 < len(text) and text[i + 1] == "'":
                        current += text[i + 1]
                        i += 2
                        continue
                    in_string = False
                    tokens.append(current)
                    current = ""
            elif in_template:
                current += ch
                if ch == "|":
                    in_template = False
                    tokens.append(current)
                    current = ""
            else:
                if ch == "'":
                    if current:
                        tokens.append(current)
                        current = ""
                    in_string = True
                    current = ch
                elif ch == "|":
                    if current:
                        tokens.append(current)
                        current = ""
                    in_template = True
                    current = ch
                elif ch in (" ", "\t", "\n", "\r"):
                    if current:
                        tokens.append(current)
                        current = ""
                else:
                    current += ch
            i += 1
        if current:
            tokens.append(current)
        return tokens

    # ------------------------------------------------------------------
    # Statement classification
    # ------------------------------------------------------------------

    def _classify_statement(self, text: str) -> AbapStatementType:
        """Determine the AbapStatementType from the statement text."""
        upper = text.upper().strip()
        tokens_upper = upper.split()
        if not tokens_upper:
            return AbapStatementType.UNKNOWN

        first = tokens_upper[0]
        second = tokens_upper[1] if len(tokens_upper) > 1 else ""

        # CLASS ... DEFINITION / CLASS ... IMPLEMENTATION
        if first == "CLASS":
            if "DEFINITION" in upper:
                return AbapStatementType.CLASS_DEFINITION
            elif "IMPLEMENTATION" in upper:
                return AbapStatementType.CLASS_IMPLEMENTATION
            # Bare CLASS is still treated as class definition
            return AbapStatementType.CLASS_DEFINITION

        # Two-word keywords
        pair = (first, second)
        if pair in _TWO_WORD_KEYWORDS:
            return _TWO_WORD_KEYWORDS[pair]

        # FIELD-SYMBOLS (single word variant already in map)
        if first == "FIELD-SYMBOLS":
            return AbapStatementType.FIELD_SYMBOLS

        # EXEC SQL (already handled above via two-word map)

        # Single-word map
        if first in _SINGLE_WORD_KEYWORDS:
            return _SINGLE_WORD_KEYWORDS[first]

        return AbapStatementType.UNKNOWN

    # ------------------------------------------------------------------
    # AST builder
    # ------------------------------------------------------------------

    def _build_ast(
        self,
        stmt_tuples: List[Tuple[str, int]],
        program: AbapProgram,
    ):
        """Walk through preprocessed statements and populate *program*."""
        idx = 0
        # For tracking FORM...ENDFORM bodies
        current_form: Optional[AbapFormRoutine] = None
        # For tracking SELECT...ENDSELECT
        pending_select: Optional[AbapSelectStatement] = None
        # For tracking EXEC SQL...ENDEXEC
        in_exec_sql = False
        exec_sql_lines: List[str] = []
        exec_sql_line_num = 0

        while idx < len(stmt_tuples):
            text, line_num = stmt_tuples[idx]
            stype = self._classify_statement(text)
            tokens = self._tokenize(text)

            stmt = AbapStatement(
                type=stype,
                raw_text=text,
                line_number=line_num,
                tokens=tokens,
            )

            # ----- EXEC SQL handling -----
            if in_exec_sql:
                if stype == AbapStatementType.ENDEXEC:
                    in_exec_sql = False
                    # Build an exec-sql select entry
                    sql_body = " ".join(exec_sql_lines)
                    sql_upper = sql_body.upper()
                    if sql_upper.lstrip().startswith("SELECT"):
                        sel = AbapSelectStatement(
                            is_exec_sql=True,
                            line_number=exec_sql_line_num,
                            raw_text=sql_body,
                        )
                        tables = self._extract_table_names(sql_body)
                        sel.from_tables = tables
                        sel.join_tables = self._extract_join_tables(sql_body)
                        program.select_statements.append(sel)
                        for t in tables + sel.join_tables:
                            program.tables_used.add(t)
                        stmt.select = sel
                    program.statements.append(stmt)
                    idx += 1
                    continue
                else:
                    exec_sql_lines.append(text)
                    idx += 1
                    continue

            if stype == AbapStatementType.EXEC_SQL:
                in_exec_sql = True
                exec_sql_lines = []
                exec_sql_line_num = line_num
                program.has_exec_sql = True
                program.statements.append(stmt)
                idx += 1
                continue

            # ----- REPORT / PROGRAM -----
            if stype in (AbapStatementType.REPORT, AbapStatementType.PROGRAM):
                self._parse_report_program(text, stype, program)
                program.statements.append(stmt)
                idx += 1
                continue

            # ----- INCLUDE -----
            if stype == AbapStatementType.INCLUDE:
                inc_name = self._parse_include(text)
                if inc_name:
                    program.includes.append(inc_name)
                program.statements.append(stmt)
                idx += 1
                continue

            # ----- TABLES (obsolete) -----
            if stype == AbapStatementType.TABLES:
                tbl = self._parse_tables_declaration(text)
                if tbl:
                    program.tables_declarations.append(tbl)
                    program.tables_used.add(tbl.upper())
                program.statements.append(stmt)
                idx += 1
                continue

            # ----- RANGES -----
            if stype == AbapStatementType.RANGES:
                rng = self._parse_ranges_declaration(text)
                if rng:
                    program.ranges_declarations.append(rng)
                program.statements.append(stmt)
                idx += 1
                continue

            # ----- DATA / CONSTANTS -----
            if stype in (AbapStatementType.DATA, AbapStatementType.CONSTANTS):
                decl = self._parse_data_declaration(text, line_num)
                if decl:
                    program.data_declarations.append(decl)
                    stmt.data_decl = decl
                program.statements.append(stmt)
                idx += 1
                continue

            # ----- TYPES -----
            if stype == AbapStatementType.TYPES:
                # We still record a data-declaration-like entry for types
                decl = self._parse_data_declaration(text, line_num)
                if decl:
                    program.data_declarations.append(decl)
                    stmt.data_decl = decl
                program.statements.append(stmt)
                idx += 1
                continue

            # ----- FIELD-SYMBOLS -----
            if stype == AbapStatementType.FIELD_SYMBOLS:
                fs_name = self._parse_field_symbol(text)
                if fs_name:
                    program.field_symbols.append(fs_name)
                program.statements.append(stmt)
                idx += 1
                continue

            # ----- SELECT -----
            if stype == AbapStatementType.SELECT:
                sel = self._parse_select(text, line_num)
                stmt.select = sel
                program.select_statements.append(sel)
                for t in sel.from_tables + sel.join_tables:
                    program.tables_used.add(t.upper())
                program.statements.append(stmt)
                # If INTO is not present in the text and no SINGLE, mark for endselect
                if not sel.is_single:
                    pending_select = sel
                idx += 1
                continue

            # ----- ENDSELECT -----
            if stype == AbapStatementType.ENDSELECT:
                if pending_select is not None:
                    pending_select.uses_endselect = True
                    pending_select = None
                program.statements.append(stmt)
                idx += 1
                continue

            # ----- CALL FUNCTION -----
            if stype == AbapStatementType.CALL_FUNCTION:
                fc = self._parse_function_call(text, line_num)
                stmt.function_call = fc
                program.function_calls.append(fc)
                program.function_modules_used.add(fc.function_name)
                if fc.is_bapi:
                    program.bapis_used.add(fc.function_name)
                program.statements.append(stmt)
                idx += 1
                continue

            # ----- PERFORM -----
            if stype == AbapStatementType.PERFORM:
                program.statements.append(stmt)
                idx += 1
                continue

            # ----- FORM -----
            if stype == AbapStatementType.FORM:
                form = self._parse_form_header(text, line_num)
                current_form = form
                program.form_routines.append(form)
                program.statements.append(stmt)
                idx += 1
                continue

            # ----- ENDFORM -----
            if stype == AbapStatementType.ENDFORM:
                current_form = None
                program.statements.append(stmt)
                idx += 1
                continue

            # ----- CLASS DEFINITION / IMPLEMENTATION -----
            if stype in (
                AbapStatementType.CLASS_DEFINITION,
                AbapStatementType.CLASS_IMPLEMENTATION,
            ):
                cls_def = self._parse_class_header(text, line_num)
                if stype == AbapStatementType.CLASS_DEFINITION:
                    program.class_definitions.append(cls_def)
                program.statements.append(stmt)
                idx += 1
                continue

            # ----- SQL-like DML (INSERT/UPDATE/DELETE/MODIFY FROM) -----
            if stype in (
                AbapStatementType.INSERT,
                AbapStatementType.UPDATE,
                AbapStatementType.DELETE,
                AbapStatementType.MODIFY,
            ):
                tables = self._extract_table_names(text)
                for t in tables:
                    program.tables_used.add(t.upper())
                if current_form is not None:
                    current_form.body_lines.append(text)
                program.statements.append(stmt)
                idx += 1
                continue

            # ----- Everything else -----
            if current_form is not None:
                current_form.body_lines.append(text)
            program.statements.append(stmt)
            idx += 1

    # ------------------------------------------------------------------
    # Individual statement parsers
    # ------------------------------------------------------------------

    def _parse_report_program(
        self, text: str, stype: AbapStatementType, program: AbapProgram
    ):
        """Parse REPORT or PROGRAM statement to extract the name."""
        tokens = self._tokenize(text)
        if len(tokens) >= 2:
            program.report_name = tokens[1]
        if stype == AbapStatementType.REPORT:
            program.program_type = "REPORT"
        else:
            program.program_type = "PROGRAM"

    def _parse_include(self, text: str) -> str:
        """Extract include name from INCLUDE statement."""
        tokens = self._tokenize(text)
        if len(tokens) >= 2:
            return tokens[1]
        return ""

    def _parse_tables_declaration(self, text: str) -> str:
        """Extract table name from TABLES statement."""
        tokens = self._tokenize(text)
        if len(tokens) >= 2:
            return tokens[1].rstrip(".")
        return ""

    def _parse_ranges_declaration(self, text: str) -> str:
        """Extract range variable name from RANGES statement."""
        tokens = self._tokenize(text)
        if len(tokens) >= 2:
            return tokens[1].rstrip(".")
        return ""

    def _parse_data_declaration(self, text: str, line_num: int) -> Optional[AbapDataDeclaration]:
        """Parse DATA, CONSTANTS, or TYPES declaration.

        Handles patterns like:
            DATA lv_name TYPE type_name VALUE 'val'.
            DATA lt_tab TYPE TABLE OF type_name.
            DATA lv_name LIKE sy-subrc.
            DATA: BEGIN OF ls_struc, ... END OF ls_struc.
        """
        tokens = self._tokenize(text)
        if len(tokens) < 2:
            return None

        # Skip the keyword (DATA / CONSTANTS / TYPES)
        name = tokens[1]

        # BEGIN OF / END OF are structural markers -- skip them
        if name.upper() in ("BEGIN", "END"):
            return AbapDataDeclaration(
                name=text.strip(),
                line_number=line_num,
                raw_text=text,
            )

        decl = AbapDataDeclaration(name=name, line_number=line_num, raw_text=text)

        upper_tokens = [t.upper() for t in tokens]

        # TYPE clause
        if "TYPE" in upper_tokens:
            type_idx = upper_tokens.index("TYPE")
            remaining = upper_tokens[type_idx + 1:]
            remaining_orig = tokens[type_idx + 1:]

            # TABLE OF / STANDARD TABLE OF / SORTED TABLE OF / HASHED TABLE OF
            if remaining and remaining[0] in (
                "TABLE",
                "STANDARD",
                "SORTED",
                "HASHED",
                "RANGE",
            ):
                decl.is_table = True
                if remaining[0] == "TABLE" and len(remaining) > 1 and remaining[1] == "OF":
                    decl.table_type = "STANDARD TABLE"
                    decl.type_ref = remaining_orig[2] if len(remaining_orig) > 2 else ""
                elif remaining[0] in ("STANDARD", "SORTED", "HASHED"):
                    tbl_kind = remaining[0] + " TABLE"
                    decl.table_type = tbl_kind
                    # Find OF
                    if "OF" in remaining:
                        of_idx = remaining.index("OF")
                        decl.type_ref = remaining_orig[of_idx + 1] if of_idx + 1 < len(remaining_orig) else ""
                elif remaining[0] == "RANGE":
                    decl.table_type = "RANGE"
                    if "OF" in remaining:
                        of_idx = remaining.index("OF")
                        decl.type_ref = remaining_orig[of_idx + 1] if of_idx + 1 < len(remaining_orig) else ""
                else:
                    decl.type_ref = remaining_orig[0] if remaining_orig else ""
            elif remaining and remaining[0] == "REF":
                # TYPE REF TO classname
                if len(remaining) > 2 and remaining[1] == "TO":
                    decl.type_ref = "REF TO " + (remaining_orig[2] if len(remaining_orig) > 2 else "")
                else:
                    decl.type_ref = " ".join(remaining_orig)
            else:
                decl.type_ref = remaining_orig[0] if remaining_orig else ""
        # LIKE clause
        elif "LIKE" in upper_tokens:
            like_idx = upper_tokens.index("LIKE")
            remaining_orig = tokens[like_idx + 1:]
            if remaining_orig:
                # LIKE LINE OF / LIKE TABLE OF
                if remaining_orig[0].upper() == "LINE" and len(remaining_orig) > 2 and remaining_orig[1].upper() == "OF":
                    decl.like_ref = "LINE OF " + remaining_orig[2]
                elif remaining_orig[0].upper() == "TABLE" and len(remaining_orig) > 2 and remaining_orig[1].upper() == "OF":
                    decl.like_ref = "TABLE OF " + remaining_orig[2]
                    decl.is_table = True
                else:
                    decl.like_ref = remaining_orig[0]

        # VALUE clause
        if "VALUE" in upper_tokens:
            val_idx = upper_tokens.index("VALUE")
            if val_idx + 1 < len(tokens):
                val = tokens[val_idx + 1]
                # Strip surrounding quotes
                if val.startswith("'") and val.endswith("'"):
                    val = val[1:-1]
                decl.value = val

        return decl

    def _parse_field_symbol(self, text: str) -> str:
        """Extract field-symbol name from FIELD-SYMBOLS declaration."""
        # Pattern: FIELD-SYMBOLS <fs_name> TYPE ...
        match = re.search(r'<\s*(\S+?)\s*>', text)
        if match:
            return "<" + match.group(1) + ">"
        return ""

    def _parse_select(self, text: str, line_num: int) -> AbapSelectStatement:
        """Parse a SELECT statement.

        Handles:
            SELECT SINGLE field1 field2 FROM table INTO (var1, var2) WHERE ...
            SELECT field1 field2 FROM table INTO TABLE lt_tab WHERE ...
            SELECT * FROM table WHERE ...
            SELECT ... FOR ALL ENTRIES IN ...
        """
        sel = AbapSelectStatement(line_number=line_num, raw_text=text)
        upper = text.upper()
        tokens = self._tokenize(text)
        upper_tokens = [t.upper() for t in tokens]

        if not upper_tokens:
            return sel

        # Pointer past SELECT keyword
        pos = 1

        # SINGLE?
        if pos < len(upper_tokens) and upper_tokens[pos] == "SINGLE":
            sel.is_single = True
            pos += 1

        # Gather target fields until FROM
        while pos < len(upper_tokens) and upper_tokens[pos] != "FROM":
            sel.target_fields.append(tokens[pos])
            pos += 1

        # FROM clause - extract table names
        if pos < len(upper_tokens) and upper_tokens[pos] == "FROM":
            pos += 1
            # The next token(s) are table names (could be joined)
            while pos < len(upper_tokens) and upper_tokens[pos] not in (
                "INTO", "WHERE", "ORDER", "GROUP", "HAVING",
                "UP", "FOR", "APPENDING",
            ):
                tok = upper_tokens[pos]
                if tok in ("INNER", "LEFT", "RIGHT", "OUTER", "CROSS", "JOIN", "ON", "AS"):
                    if tok == "JOIN":
                        # Next token is a join table
                        if pos + 1 < len(upper_tokens):
                            sel.join_tables.append(tokens[pos + 1])
                            pos += 1
                    pos += 1
                    continue
                # Skip keywords that might appear
                if tok in ("AND", "OR", "NOT", "=", "<>", "<", ">", "<=", ">=", "LIKE", "IN", "BETWEEN"):
                    break
                sel.from_tables.append(tokens[pos])
                pos += 1

        # INTO clause
        into_start = -1
        for i, t in enumerate(upper_tokens):
            if t == "INTO":
                into_start = i
                break
        if into_start >= 0:
            into_parts = []
            j = into_start + 1
            while j < len(upper_tokens) and upper_tokens[j] not in ("WHERE", "ORDER", "GROUP", "HAVING", "FOR"):
                into_parts.append(tokens[j])
                j += 1
            sel.into_clause = " ".join(into_parts)
            # If INTO TABLE ... then it does not need ENDSELECT
            if "TABLE" in [p.upper() for p in into_parts]:
                sel.is_single = sel.is_single  # keep as-is, no endselect needed
            elif not sel.is_single:
                sel.uses_endselect = True

        # APPENDING TABLE also means no ENDSELECT needed
        if "APPENDING" in upper_tokens:
            sel.uses_endselect = False

        # WHERE clause
        where_start = -1
        for i, t in enumerate(upper_tokens):
            if t == "WHERE":
                where_start = i
                break
        if where_start >= 0:
            where_parts = tokens[where_start + 1:]
            sel.where_clause = " ".join(where_parts)

        # Extract additional join tables from the raw text
        for match in re.finditer(r'\bJOIN\s+(\S+)', upper):
            join_tbl = text[match.start(1):match.end(1)]
            if join_tbl not in sel.join_tables:
                sel.join_tables.append(join_tbl)

        return sel

    def _parse_function_call(self, text: str, line_num: int) -> AbapFunctionCall:
        """Parse CALL FUNCTION statement.

        Pattern:
            CALL FUNCTION 'FM_NAME'
                EXPORTING param1 = val1
                           param2 = val2
                IMPORTING param3 = val3
                TABLES    param4 = val4
                EXCEPTIONS param5 = 1.
        """
        fc = AbapFunctionCall(function_name="", line_number=line_num, raw_text=text)

        # Extract function module name (quoted)
        name_match = re.search(
            r"CALL\s+FUNCTION\s+'([^']+)'",
            text,
            re.IGNORECASE,
        )
        if name_match:
            fc.function_name = name_match.group(1)

        # Check if BAPI
        if fc.function_name.upper().startswith("BAPI_"):
            fc.is_bapi = True

        # Parse parameter sections
        upper = text.upper()
        # Find section positions
        section_keywords = ["EXPORTING", "IMPORTING", "TABLES", "EXCEPTIONS",
                            "CHANGING", "RECEIVING"]
        positions: List[Tuple[str, int]] = []
        for kw in section_keywords:
            # Find all occurrences of the keyword as a standalone word
            for m in re.finditer(r'\b' + kw + r'\b', upper):
                positions.append((kw, m.start()))
        positions.sort(key=lambda x: x[1])

        for i, (kw, start) in enumerate(positions):
            end = positions[i + 1][1] if i + 1 < len(positions) else len(text)
            section_text = text[start + len(kw):end].strip()
            params = self._parse_fm_params(section_text)
            if kw == "EXPORTING":
                fc.exporting = params
            elif kw == "IMPORTING":
                fc.importing = params
            elif kw == "TABLES":
                fc.tables = params
            elif kw == "EXCEPTIONS":
                fc.exceptions = params
            # CHANGING and RECEIVING are mapped into exporting for simplicity

        return fc

    def _parse_fm_params(self, section_text: str) -> Dict[str, str]:
        """Parse parameter assignments like 'param1 = val1 param2 = val2'."""
        params: Dict[str, str] = {}
        # Split on spaces, find name = value patterns
        tokens = self._tokenize(section_text)
        i = 0
        while i < len(tokens):
            if i + 2 < len(tokens) and tokens[i + 1] == "=":
                name = tokens[i]
                value = tokens[i + 2]
                params[name] = value
                i += 3
            else:
                i += 1
        return params

    def _parse_form_header(self, text: str, line_num: int) -> AbapFormRoutine:
        """Parse FORM statement header.

        Pattern: FORM routine_name [USING p1 p2] [CHANGING p3 p4].
        """
        tokens = self._tokenize(text)
        name = tokens[1] if len(tokens) > 1 else ""
        params: List[str] = []

        upper_tokens = [t.upper() for t in tokens]
        # Collect parameters from USING / CHANGING / TABLES sections
        collecting = False
        for i, tok in enumerate(upper_tokens):
            if tok in ("USING", "CHANGING", "TABLES"):
                collecting = True
                continue
            if collecting:
                # Skip type declarations within parameters
                if tok in ("TYPE", "LIKE", "STRUCTURE", "VALUE"):
                    # Skip this and next token
                    collecting = False
                    continue
                if tok.startswith("(") or tok.startswith("<"):
                    params.append(tokens[i])
                elif not tok.startswith("'"):
                    params.append(tokens[i])

        return AbapFormRoutine(name=name, parameters=params, line_number=line_num)

    def _parse_class_header(self, text: str, line_num: int) -> AbapClassDefinition:
        """Parse CLASS statement header.

        Pattern: CLASS lcl_name DEFINITION [INHERITING FROM superclass]
                                           [CREATE PUBLIC|PRIVATE|PROTECTED].
        """
        tokens = self._tokenize(text)
        upper_tokens = [t.upper() for t in tokens]

        name = tokens[1] if len(tokens) > 1 else ""
        cls = AbapClassDefinition(name=name, line_number=line_num)

        # INHERITING FROM
        if "INHERITING" in upper_tokens:
            inh_idx = upper_tokens.index("INHERITING")
            if inh_idx + 2 < len(tokens) and upper_tokens[inh_idx + 1] == "FROM":
                cls.superclass = tokens[inh_idx + 2]

        # Detect if global class (names starting with Z/Y or /namespace/ are typically global)
        name_upper = name.upper()
        if name_upper.startswith("ZCL_") or name_upper.startswith("YCL_") or name_upper.startswith("/"):
            cls.is_local = False
        elif name_upper.startswith("LCL_") or name_upper.startswith("CL_"):
            cls.is_local = name_upper.startswith("LCL_")

        return cls

    # ------------------------------------------------------------------
    # Table name extraction helpers
    # ------------------------------------------------------------------

    def _extract_table_names(self, text: str) -> List[str]:
        """Extract table names from SQL-like clauses: FROM, INTO, UPDATE, JOIN.

        Used for INSERT/UPDATE/DELETE/MODIFY statements as well as SELECT.
        Returns deduplicated list preserving order.
        """
        tables: List[str] = []
        upper = text.upper()
        tokens = self._tokenize(text)
        upper_tokens = [t.upper() for t in tokens]

        # FROM table
        for i, tok in enumerate(upper_tokens):
            if tok == "FROM" and i + 1 < len(upper_tokens):
                candidate = tokens[i + 1]
                if self._is_table_name(candidate):
                    tables.append(candidate)

        # INTO table (for INSERT INTO)
        for i, tok in enumerate(upper_tokens):
            if tok == "INTO" and i + 1 < len(upper_tokens):
                candidate = tokens[i + 1]
                # Only consider if not a variable (starts with a letter, no parens)
                if self._is_table_name(candidate) and not candidate.startswith("(") and not candidate.startswith("@"):
                    # For INSERT INTO, the token after INTO is a table
                    # For SELECT INTO, it is a variable -- differentiate by context
                    if i > 0 and upper_tokens[0] in ("INSERT",):
                        tables.append(candidate)

        # UPDATE table SET ...
        if upper_tokens and upper_tokens[0] == "UPDATE" and len(upper_tokens) > 1:
            candidate = tokens[1]
            if self._is_table_name(candidate):
                tables.append(candidate)

        # DELETE FROM table
        if upper_tokens and upper_tokens[0] == "DELETE":
            if "FROM" in upper_tokens:
                from_idx = upper_tokens.index("FROM")
                if from_idx + 1 < len(upper_tokens):
                    candidate = tokens[from_idx + 1]
                    if self._is_table_name(candidate):
                        tables.append(candidate)
            elif len(upper_tokens) > 1:
                candidate = tokens[1]
                if self._is_table_name(candidate) and candidate.upper() not in (
                    "ADJACENT", "LEADING", "TRAILING",
                ):
                    tables.append(candidate)

        # MODIFY table FROM ...
        if upper_tokens and upper_tokens[0] == "MODIFY" and len(upper_tokens) > 1:
            candidate = tokens[1]
            if self._is_table_name(candidate) and candidate.upper() != "TABLE":
                tables.append(candidate)

        # INSERT into table (no INTO keyword): INSERT table FROM ...
        if upper_tokens and upper_tokens[0] == "INSERT" and len(upper_tokens) > 1:
            candidate = tokens[1]
            if self._is_table_name(candidate) and candidate.upper() not in ("INTO", "LINES", "INITIAL"):
                tables.append(candidate)

        # JOIN tables
        tables.extend(self._extract_join_tables(text))

        # Deduplicate preserving order
        seen = set()
        result = []
        for t in tables:
            key = t.upper()
            if key not in seen:
                seen.add(key)
                result.append(t)
        return result

    def _extract_join_tables(self, text: str) -> List[str]:
        """Extract table names from JOIN clauses."""
        tables: List[str] = []
        for m in re.finditer(r'\bJOIN\s+(\S+)', text, re.IGNORECASE):
            candidate = m.group(1)
            if self._is_table_name(candidate):
                tables.append(candidate)
        return tables

    @staticmethod
    def _is_table_name(token: str) -> bool:
        """Heuristic: check if a token looks like a DB table name.

        ABAP table names are alphanumeric, may contain _, /, and -.
        They should not start with special characters or be pure numbers.
        """
        if not token:
            return False
        # Skip string literals, parenthesized expressions, field-symbols
        if token.startswith("'") or token.startswith("(") or token.startswith("<"):
            return False
        if token.startswith("@"):
            return False
        # Must start with a letter or /
        first = token[0]
        if not (first.isalpha() or first == "/"):
            return False
        # Must not be an ABAP keyword used in SQL context
        kw = token.upper()
        if kw in (
            "INTO", "FROM", "WHERE", "SET", "VALUES", "TABLE", "APPENDING",
            "CORRESPONDING", "FIELDS", "SINGLE", "DISTINCT", "ALL",
            "ORDER", "BY", "GROUP", "HAVING", "UP", "TO", "ROWS",
            "FOR", "UPDATE", "CLIENT", "SPECIFIED", "BYPASSING", "BUFFER",
            "INNER", "LEFT", "RIGHT", "OUTER", "CROSS", "JOIN", "ON", "AS",
            "AND", "OR", "NOT", "IN", "BETWEEN", "LIKE", "IS", "NULL",
            "EXISTS", "SOME", "ANY", "UNION", "INTERSECT", "EXCEPT",
            "USING", "CHANGING", "EXPORTING", "IMPORTING", "EXCEPTIONS",
            "WITH", "ENDSELECT", "CONNECTION",
        ):
            return False
        return True


# ---------------------------------------------------------------------------
# Convenience functions
# ---------------------------------------------------------------------------

def parse_abap_file(filepath: str, encoding: str = "utf-8") -> AbapProgram:
    """Parse an ABAP source file and return an AbapProgram AST."""
    parser = AbapParser(encoding=encoding)
    return parser.parse_file(filepath)


def parse_abap_string(source: str) -> AbapProgram:
    """Parse ABAP source code from a string and return an AbapProgram AST."""
    parser = AbapParser()
    return parser.parse_string(source)
