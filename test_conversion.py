"""
SAP ECC to S/4HANA Migration Tool - Smoke Test
"""
import os
import sys
import traceback

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from src.abap_parser import AbapParser, parse_abap_string
from src.s4_transformer import S4Transformer, MigrationOptions
from src.abap_generator import AbapCodeGenerator
from src.report_generator import ReportGenerator


def test_parser():
    """Test ABAP parser with inline source."""
    print("=" * 60)
    print("TEST 1: ABAP Parser")
    print("=" * 60)

    source = """
REPORT z_test_program.

TABLES: lfa1.

DATA: gv_bukrs TYPE bukrs,
      gv_total TYPE p DECIMALS 2.

RANGES: r_bukrs FOR lfa1-bukrs.

MOVE gv_bukrs TO gv_total.
COMPUTE gv_total = gv_total * 100.
ADD 10 TO gv_total.
SUBTRACT 5 FROM gv_total.

SELECT * FROM bsik
  INTO CORRESPONDING FIELDS OF gs_item
  WHERE bukrs = gv_bukrs.
  WRITE: / gs_item-dmbtr.
ENDSELECT.

CALL FUNCTION 'BAPI_VENDOR_GETDETAIL'
  EXPORTING
    vendorno = gv_lifnr
  IMPORTING
    return   = ls_return.

EXEC SQL.
  SELECT balance FROM zbalance INTO :gv_total
ENDEXEC.

FORM calc_total USING p_amount TYPE p.
  MULTIPLY p_amount BY 2.
  DIVIDE p_amount BY 3.
ENDFORM.
"""

    program = parse_abap_string(source)
    print(f"  Program ID: {program.program_id}")
    print(f"  Statements: {len(program.statements)}")
    print(f"  Data declarations: {len(program.data_declarations)}")
    print(f"  SELECT statements: {len(program.select_statements)}")
    print(f"  Function calls: {len(program.function_calls)}")
    print(f"  FORM routines: {len(program.form_routines)}")
    print(f"  Tables used: {program.tables_used}")
    print(f"  Function modules: {program.function_modules_used}")
    print("  PASSED")
    return program


def test_transformer(program):
    """Test S4 transformer."""
    print("\n" + "=" * 60)
    print("TEST 2: S/4HANA Transformer")
    print("=" * 60)

    options = MigrationOptions(
        modernize_syntax=True,
        convert_tables=True,
        convert_bapis=True,
        convert_fm=True,
    )
    transformer = S4Transformer(options)
    result = transformer.transform(program, "test_source.abap")

    print(f"  Auto-converted: {result.auto_converted}")
    print(f"  Needs review: {result.needs_review}")
    print(f"  Manual only: {result.manual_only}")
    print(f"  Total changes: {len(result.changes)}")
    for change in result.changes:
        print(f"    [{change.severity}] {change.category}: {change.old_value} → {change.new_value}")
    print("  PASSED")
    return result


def test_generator(result):
    """Test code generator."""
    print("\n" + "=" * 60)
    print("TEST 3: ABAP Code Generator")
    print("=" * 60)

    options = MigrationOptions()
    generator = AbapCodeGenerator(options)

    output_dir = os.path.join(BASE_DIR, "output", "test")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "z_test_program_s4.abap")
    generator.generate(result, output_path)

    if os.path.exists(output_path):
        size = os.path.getsize(output_path)
        print(f"  Output file: {output_path}")
        print(f"  File size: {size} bytes")
        print("  PASSED")
    else:
        print("  FAILED - Output file not created")
    return result


def test_report(result):
    """Test report generator."""
    print("\n" + "=" * 60)
    print("TEST 4: Report Generator")
    print("=" * 60)

    options = MigrationOptions(report_format="Both")
    reporter = ReportGenerator(options)

    output_dir = os.path.join(BASE_DIR, "output", "test")
    reporter.generate([result], output_dir)

    html_path = os.path.join(output_dir, "migration_report.html")
    csv_path = os.path.join(output_dir, "migration_report.csv")

    if os.path.exists(html_path):
        print(f"  HTML report: {html_path} ({os.path.getsize(html_path)} bytes)")
    if os.path.exists(csv_path):
        print(f"  CSV report: {csv_path} ({os.path.getsize(csv_path)} bytes)")
    print("  PASSED")


def test_sample_files():
    """Test with sample ABAP files if they exist."""
    print("\n" + "=" * 60)
    print("TEST 5: Sample File Processing")
    print("=" * 60)

    samples_dir = os.path.join(BASE_DIR, "samples")
    if not os.path.isdir(samples_dir):
        print("  SKIPPED - No samples directory")
        return

    parser = AbapParser()
    options = MigrationOptions()
    transformer = S4Transformer(options)

    for filename in os.listdir(samples_dir):
        if filename.endswith(('.abap', '.txt', '.prog')):
            filepath = os.path.join(samples_dir, filename)
            print(f"\n  Processing: {filename}")
            try:
                program = parser.parse_file(filepath)
                print(f"    Statements: {len(program.statements)}")
                print(f"    Tables: {program.tables_used}")

                result = transformer.transform(program, filename)
                print(f"    Changes: {len(result.changes)} "
                      f"(auto={result.auto_converted}, "
                      f"review={result.needs_review}, "
                      f"manual={result.manual_only})")
                print(f"    PASSED")
            except Exception as e:
                print(f"    FAILED: {e}")
                traceback.print_exc()


def main():
    print("SAP ECC to S/4HANA Migration Tool - Smoke Test")
    print("=" * 60)

    try:
        program = test_parser()
        result = test_transformer(program)
        test_generator(result)
        test_report(result)
        test_sample_files()

        print("\n" + "=" * 60)
        print("ALL TESTS PASSED")
        print("=" * 60)

    except Exception as e:
        print(f"\nTEST FAILED: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
