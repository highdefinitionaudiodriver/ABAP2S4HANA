"""
ABAP2S4HANA プロジェクト設計書生成スクリプト
ソースコードを解析し、design_document.xlsx を出力する
"""
import os
import sys

try:
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter
except ImportError:
    print("openpyxl が見つかりません。インストールします...")
    os.system(f"{sys.executable} -m pip install openpyxl")
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_PATH = os.path.join(BASE_DIR, "design_document.xlsx")

# ============================================================
# スタイル定義
# ============================================================
HEADER_FONT = Font(name="Meiryo", size=11, bold=True, color="FFFFFF")
HEADER_FILL = PatternFill(start_color="2C3E50", end_color="2C3E50", fill_type="solid")
BODY_FONT = Font(name="Meiryo", size=10)
TITLE_FONT = Font(name="Meiryo", size=14, bold=True, color="2C3E50")
THIN_BORDER = Border(
    left=Side(style="thin"),
    right=Side(style="thin"),
    top=Side(style="thin"),
    bottom=Side(style="thin"),
)
WRAP_ALIGNMENT = Alignment(wrap_text=True, vertical="top")


def apply_header_row(ws, row, col_count):
    for col in range(1, col_count + 1):
        cell = ws.cell(row=row, column=col)
        cell.font = HEADER_FONT
        cell.fill = HEADER_FILL
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = THIN_BORDER


def apply_body_cell(ws, row, col, value, wrap=False):
    cell = ws.cell(row=row, column=col, value=value)
    cell.font = BODY_FONT
    cell.border = THIN_BORDER
    if wrap:
        cell.alignment = WRAP_ALIGNMENT
    else:
        cell.alignment = Alignment(vertical="top")
    return cell


def set_col_widths(ws, widths):
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w


def add_title_row(ws, title, col_count):
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=col_count)
    cell = ws.cell(row=1, column=1, value=title)
    cell.font = TITLE_FONT
    cell.alignment = Alignment(vertical="center")
    ws.row_dimensions[1].height = 30


# ============================================================
# Sheet 1: 機能一覧表
# ============================================================
def create_feature_list(wb):
    ws = wb.active
    ws.title = "1_機能一覧表"

    headers = ["機能ID", "機能名", "機能概要", "対応モジュール", "対象ユーザー",
               "実装ファイル", "入力", "出力", "備考"]
    col_count = len(headers)
    add_title_row(ws, "機能一覧表（基本設計）— SAP ECC to S/4HANA Migration Tool", col_count)

    row = 3
    for c, h in enumerate(headers, 1):
        ws.cell(row=row, column=c, value=h)
    apply_header_row(ws, row, col_count)

    features = [
        ("F-001", "ABAPソースコード解析",
         "ABAPソースファイル(.abap/.txt/.prog)を読み込み、構文解析を行いAST(抽象構文木)を生成する。"
         "REPORT名、DATA宣言、SELECT文、CALL FUNCTION文、FORM/CLASS定義、TABLES/RANGES宣言、EXEC SQL等を検出し構造化する。"
         "INCLUDE文の再帰的解決にも対応。",
         "全モジュール共通", "ABAPコンサルタント\nマイグレーション担当者",
         "src/abap_parser.py",
         "ABAPソースファイル\n(単一ファイル or ディレクトリ)",
         "AbapProgram AST オブジェクト",
         "90種以上のABAPステートメントタイプを認識。チェーン文展開・インラインコメント除去・複数行結合の前処理を実施。"),

        ("F-002", "S/4HANA変換ルール適用",
         "解析済みASTに対し、SAP Simplification Listに基づく変換ルールを適用する。"
         "テーブル名置換(BSEG→ACDOCA等)、BAPI/汎用モジュール置換、"
         "SQL構文モダナイズ、廃止構文変換(MOVE/COMPUTE/ADD等)、"
         "EXEC SQL検出、SELECT...ENDSELECTループ検出を実施。",
         "FI/CO, MM, SD, BP, PP", "ABAPコンサルタント\nマイグレーション担当者",
         "src/s4_transformer.py",
         "AbapProgram AST\nMigrationOptions",
         "TransformResult\n(変換済み行 + 変更記録リスト)",
         "変更にはAUTO/REVIEW/MANUALの3段階の深刻度レベルを付与。SAPモジュールフィルタで対象を絞り込み可能。"),

        ("F-003", "変換済みABAPコード生成",
         "変換結果をもとにS/4HANA対応済みABAPソースファイルを出力する。"
         "各変更箇所にマイグレーションコメント(AUTO/REVIEW/MANUAL)を付加。"
         "ファイルヘッダにマイグレーションメタ情報を記載。",
         "全モジュール共通", "ABAPコンサルタント\nマイグレーション担当者",
         "src/abap_generator.py",
         "TransformResult\n出力パス",
         "変換済み .abap ファイル\n(接尾辞 _s4)",
         "バッチ生成にも対応。ディレクトリ構造を保持して出力。"),

        ("F-004", "影響分析レポート生成",
         "変換結果をHTML/CSV形式のレポートとして出力する。"
         "総変更数・自動変換数・レビュー必要数・手動変換数のサマリ、"
         "SAPモジュール別・カテゴリ別の内訳表、ファイル別詳細(折り畳み可能)、"
         "マニュアルアクション項目リスト、ドーナツチャートによる可視化を含む。",
         "全モジュール共通", "プロジェクトマネージャ\nABAPコンサルタント",
         "src/report_generator.py",
         "TransformResult リスト\n出力ディレクトリ",
         "migration_report.html\nmigration_report.csv",
         "ダッシュボードにSVGドーナツチャート・ファイル別レディネスバー・変更ストリーム(フィルタ可能)を配置。"),

        ("F-005", "Simplificationルール管理",
         "SAP Simplification List for S/4HANA 2023 に基づく変換ルールの定義と管理。"
         "テーブル置換ルール(16件)、BAPI置換ルール、汎用モジュール置換ルール、"
         "ABAP構文モダナイズルール(8件)、SQLルール(5件)、SELECT書換ルール(6件)を内蔵。"
         "ルールIDによる検索、モジュール/カテゴリ/深刻度によるフィルタリングが可能。",
         "FI/CO, MM, SD, BP, PP, ABAP", "ABAPコンサルタント",
         "src/simplification_rules.py",
         "ソースバージョン\nターゲットバージョン",
         "SimplificationRule リスト\n各種マッピング辞書",
         "ルールにはフィールドマッピング情報も含む。auto_fixフラグで自動修正可否を制御。"),

        ("F-006", "SAPモジュール判定・フィールドマッピング",
         "使用テーブル名・汎用モジュール名からSAPモジュール(FI/CO/MM/SD/BP/PP)を自動判定。"
         "テーブル間のフィールドマッピング(BSEG→ACDOCA, MSEG→MATDOC等 14パターン)、"
         "廃止トランザクションコード情報(29件)、CDS Viewの置換情報(17件)を提供。",
         "FI/CO, MM, SD, BP, PP", "ABAPコンサルタント",
         "src/vendor_modules.py",
         "テーブル名セット\n汎用モジュール名セット",
         "SapModuleType セット\nフィールドマッピング辞書\nCDS View情報",
         "113テーブル、18汎用モジュールプレフィックスの対応マスタデータを内蔵。"),

        ("F-007", "GUIアプリケーション",
         "tkinter ベースのGUIアプリケーション。"
         "入出力フォルダ指定、ソース/ターゲットバージョン選択、エンコーディング設定、"
         "ファイル拡張子フィルタ、SAPモジュールフィルタ、変換オプション(7種チェックボックス)、"
         "リアルタイムログ表示(色分き)、プログレスバー、キャンセル機能を提供。",
         "全モジュール共通", "全ユーザー",
         "main.py",
         "ユーザーGUI入力",
         "変換済みファイル\nレポート",
         "スレッドベースの非同期処理。59言語のUIローカライズに対応。"),

        ("F-008", "CLIモード実行",
         "コマンドライン引数(-i, -o)指定によるGUI無し実行。"
         "ソース/ターゲットバージョン、エンコーディング、拡張子、モジュールフィルタ、"
         "レポート形式等を引数で指定可能。CI/CDパイプラインへの組み込みに適する。",
         "全モジュール共通", "DevOpsエンジニア\nCI/CD管理者",
         "main.py (run_cli関数)",
         "コマンドライン引数",
         "変換済みファイル\nレポート\n終了コード",
         "--no-modernize, --no-tables, --no-bapis 等の無効化フラグあり。"),

        ("F-009", "多言語対応(i18n)",
         "UIラベル・メッセージの59言語ローカライズ。"
         "言語切替はGUI上のComboboxから即時反映。"
         "翻訳辞書は辞書形式で一元管理し、フォールバックは英語。",
         "全モジュール共通", "全ユーザー",
         "src/i18n.py",
         "言語コード(en/ja/zh/ko等)",
         "翻訳済みテキスト",
         "対応言語: en, ja, zh, ko, es, pt, fr, de, it, ru, ar, hi, th, vi, id 他44言語。"),

        ("F-010", "オリジナルファイルバックアップ",
         "変換実行前にオリジナルのABAPソースファイルを_backupディレクトリにタイムスタンプ付きでバックアップ。"
         "ディレクトリ構造を保持したバッチバックアップにも対応。",
         "全モジュール共通", "ABAPコンサルタント",
         "src/abap_generator.py\n(BackupManager)",
         "ソースファイルパス\nバックアップディレクトリ",
         ".bak ファイル",
         "オプションで無効化可能(--no-backup)。"),
    ]

    for i, feat in enumerate(features):
        r = row + 1 + i
        for c, val in enumerate(feat, 1):
            apply_body_cell(ws, r, c, val, wrap=True)
        ws.row_dimensions[r].height = 80

    set_col_widths(ws, [10, 28, 55, 20, 20, 22, 22, 22, 45])
    ws.freeze_panes = "A4"


# ============================================================
# Sheet 2: API仕様書（CLIインターフェース）
# ============================================================
def create_api_spec(wb):
    ws = wb.create_sheet("2_API仕様書")

    headers = ["API ID", "インターフェース種別", "エントリポイント",
               "引数/パラメータ", "型/選択肢", "必須", "デフォルト値",
               "処理概要", "戻り値/出力"]
    col_count = len(headers)
    add_title_row(ws, "API仕様書（詳細設計）— 内部API・CLIインターフェース", col_count)

    row = 3
    for c, h in enumerate(headers, 1):
        ws.cell(row=row, column=c, value=h)
    apply_header_row(ws, row, col_count)

    apis = [
        ("CLI-001", "CLI引数", "main.py → run_cli()",
         "-i / --input", "str (ディレクトリパス)", "Yes (CLI時)", "なし",
         "入力フォルダ。ABAPソースファイルを含むディレクトリを指定。再帰的にファイルを探索する。",
         "なし (入力のみ)"),
        ("CLI-002", "CLI引数", "main.py → run_cli()",
         "-o / --output", "str (ディレクトリパス)", "Yes (CLI時)", "なし",
         "出力フォルダ。変換済みファイル・レポート・バックアップを格納する。存在しない場合は自動作成。",
         "なし (入力のみ)"),
        ("CLI-003", "CLI引数", "main.py → run_cli()",
         "-e / --encoding", "str", "No", "utf-8",
         "ソースファイルのエンコーディング。shift_jis, euc-jp, cp932, iso-8859-1, cp1252 等。",
         "なし"),
        ("CLI-004", "CLI引数", "main.py → run_cli()",
         "--ext", "str (カンマ区切り)", "No", ".abap,.txt,.prog,.ABAP",
         "処理対象のファイル拡張子。カンマ区切りで複数指定可能。",
         "なし"),
        ("CLI-005", "CLI引数", "main.py → run_cli()",
         "--source-version", "ECC 6.0 ~ ECC 6.08", "No", "ECC 6.08",
         "移行元SAPバージョン。ルール適用の基準バージョンとして使用。",
         "なし"),
        ("CLI-006", "CLI引数", "main.py → run_cli()",
         "--target-version", "S/4HANA 1709 ~ 2023", "No", "S/4HANA 2023",
         "移行先S/4HANAバージョン。ルール適用のターゲットバージョンとして使用。",
         "なし"),
        ("CLI-007", "CLI引数", "main.py → run_cli()",
         "--module", "ALL/FI/CO/MM/SD/BP/PP/ABAP Language", "No", "ALL",
         "処理対象SAPモジュールフィルタ。指定モジュールに関連するルールのみ適用。",
         "なし"),
        ("CLI-008", "CLI引数", "main.py → run_cli()",
         "--report-format", "HTML / CSV / Both", "No", "Both",
         "レポート出力形式。",
         "なし"),
        ("CLI-009", "CLI引数", "main.py → run_cli()",
         "--no-modernize", "フラグ (store_true)", "No", "False",
         "構文モダナイズ変換を無効化する。", "なし"),
        ("CLI-010", "CLI引数", "main.py → run_cli()",
         "--no-tables", "フラグ (store_true)", "No", "False",
         "テーブル名変換を無効化する。", "なし"),
        ("CLI-011", "CLI引数", "main.py → run_cli()",
         "--no-bapis", "フラグ (store_true)", "No", "False",
         "BAPI変換を無効化する。", "なし"),
        ("CLI-012", "CLI引数", "main.py → run_cli()",
         "--no-fm", "フラグ (store_true)", "No", "False",
         "汎用モジュール変換を無効化する。", "なし"),
        ("CLI-013", "CLI引数", "main.py → run_cli()",
         "--no-report", "フラグ (store_true)", "No", "False",
         "レポート生成を無効化する。", "なし"),
        ("CLI-014", "CLI引数", "main.py → run_cli()",
         "--no-backup", "フラグ (store_true)", "No", "False",
         "オリジナルファイルのバックアップを無効化する。", "なし"),

        ("PYAPI-001", "Python内部API", "AbapParser.parse_file(filepath)",
         "filepath: str", "str (ファイルパス)", "Yes", "なし",
         "ABAPソースファイルを解析しAbapProgram ASTを返す。INCLUDE文も再帰的に解決。",
         "AbapProgram オブジェクト"),
        ("PYAPI-002", "Python内部API", "AbapParser.parse_string(source)",
         "source: str", "str (ABAPソースコード)", "Yes", "なし",
         "ABAP文字列を解析しAbapProgram ASTを返す。テスト・文字列入力用。",
         "AbapProgram オブジェクト"),
        ("PYAPI-003", "Python内部API", "S4Transformer.transform(program, source_file)",
         "program: AbapProgram\nsource_file: str", "AbapProgram, str", "Yes/No", "source_file=''",
         "AST全文にS/4HANA変換ルールを適用。テーブル変換→FM変換→BAPI変換→SELECT書換→SQL構文→廃止構文→EXEC SQLの順に処理。",
         "TransformResult オブジェクト"),
        ("PYAPI-004", "Python内部API", "AbapCodeGenerator.generate(result, output_path)",
         "result: TransformResult\noutput_path: str", "TransformResult, str", "Yes", "なし",
         "変換結果をABAPソースファイルとして出力。マイグレーションコメント付加。",
         "ファイル書き出し"),
        ("PYAPI-005", "Python内部API", "ReportGenerator.generate(results, output_dir)",
         "results: List[TransformResult]\noutput_dir: str", "List, str", "Yes", "なし",
         "HTML/CSVレポートを生成。設定に応じてHTML・CSV・または両方を出力。",
         "migration_report.html\nmigration_report.csv"),
        ("PYAPI-006", "Python内部API", "detect_sap_module(tables, fms)",
         "tables_used: List[str]\nfm_used: List[str]", "Optional[List[str]]", "No", "None",
         "テーブル名・汎用モジュール名からSAPモジュールを自動判定。",
         "Set[SapModuleType]"),
        ("PYAPI-007", "Python内部API", "get_field_mapping(old_table, new_table)",
         "old_table: str\nnew_table: str", "str, str", "Yes", "なし",
         "テーブル移行時のフィールドマッピングを返す。14パターン登録済み。",
         "Dict[str, str]"),
        ("PYAPI-008", "Python内部API", "SimplificationRules.get_rule_by_id(rule_id)",
         "rule_id: str", "str", "Yes", "なし",
         "ルールIDで単一のSimplificationRuleを検索・取得。",
         "Optional[SimplificationRule]"),
        ("PYAPI-009", "Python内部API", "I18n.t(key, **kwargs)",
         "key: str, **kwargs", "str", "Yes", "なし",
         "指定された翻訳キーの現在言語のテキストを返す。フォールバックはen。{変数}の置換も対応。",
         "str (翻訳テキスト)"),
    ]

    for i, api in enumerate(apis):
        r = row + 1 + i
        for c, val in enumerate(api, 1):
            apply_body_cell(ws, r, c, val, wrap=True)
        ws.row_dimensions[r].height = 50

    set_col_widths(ws, [12, 16, 38, 28, 26, 10, 22, 50, 28])
    ws.freeze_panes = "A4"


# ============================================================
# Sheet 3: テーブル定義書 (データクラス・内部データ構造)
# ============================================================
def create_table_definitions(wb):
    ws = wb.create_sheet("3_テーブル定義書")

    headers = ["データクラス名", "フィールド名", "データ型", "デフォルト値",
               "主キー/制約", "論理名(日本語)", "説明"]
    col_count = len(headers)
    add_title_row(ws, "テーブル定義書（詳細設計）— 内部データ構造・AST定義", col_count)

    row = 3
    for c, h in enumerate(headers, 1):
        ws.cell(row=row, column=c, value=h)
    apply_header_row(ws, row, col_count)

    tables = [
        # AbapProgram
        ("AbapProgram", "report_name", "str", '""', "-", "レポート名", "ABAPプログラムのREPORT名"),
        ("AbapProgram", "program_type", "str", '""', "-", "プログラム種別", "REPORT/PROGRAM/FUNCTION-POOL等"),
        ("AbapProgram", "source_file", "str", '""', "-", "ソースファイルパス", "解析元ファイルの絶対パス"),
        ("AbapProgram", "includes", "List[str]", "[]", "-", "INCLUDEリスト", "INCLUDE文で参照されるプログラム名"),
        ("AbapProgram", "include_resolutions", "List[IncludeResolution]", "[]", "-", "INCLUDE解決結果", "各INCLUDEの解決状態と解析結果"),
        ("AbapProgram", "data_declarations", "List[AbapDataDeclaration]", "[]", "-", "DATA宣言リスト", "プログラム内のDATA/TYPES/CONSTANTS宣言"),
        ("AbapProgram", "field_symbols", "List[str]", "[]", "-", "フィールドシンボル", "FIELD-SYMBOLS宣言名"),
        ("AbapProgram", "select_statements", "List[AbapSelectStatement]", "[]", "-", "SELECT文リスト", "検出されたSELECT文すべて"),
        ("AbapProgram", "function_calls", "List[AbapFunctionCall]", "[]", "-", "汎用モジュール呼出", "CALL FUNCTIONで呼び出された汎用モジュール"),
        ("AbapProgram", "form_routines", "List[AbapFormRoutine]", "[]", "-", "FORMルーチン", "FORM~ENDFORMブロック"),
        ("AbapProgram", "class_definitions", "List[AbapClassDefinition]", "[]", "-", "クラス定義", "CLASS DEFINITION"),
        ("AbapProgram", "statements", "List[AbapStatement]", "[]", "-", "全ステートメント", "全解析済みステートメント(実行順)"),
        ("AbapProgram", "tables_used", "set", "set()", "-", "使用テーブルセット", "SELECT/UPDATE/DELETE等で参照されたテーブル名"),
        ("AbapProgram", "function_modules_used", "set", "set()", "-", "使用FMセット", "呼び出された汎用モジュール名"),
        ("AbapProgram", "bapis_used", "set", "set()", "-", "使用BAPIセット", "呼び出されたBAPI名(BAPI_プレフィックス)"),
        ("AbapProgram", "has_exec_sql", "bool", "False", "-", "EXEC SQL有無", "EXEC SQL...ENDEXEC の存在フラグ"),
        ("AbapProgram", "tables_declarations", "List[str]", "[]", "-", "TABLES宣言", "TABLES文で宣言されたテーブル名"),
        ("AbapProgram", "ranges_declarations", "List[str]", "[]", "-", "RANGES宣言", "RANGES文で宣言されたレンジ名"),
        ("AbapProgram", "comment_lines", "int", "0", "-", "コメント行数", "コメント行の数"),
        ("AbapProgram", "total_lines", "int", "0", "-", "総行数", "ソースファイルの全行数"),

        # AbapStatement
        ("AbapStatement", "type", "AbapStatementType", "-", "必須", "ステートメント種別", "90種以上のEnum値(DATA/SELECT/CALL FUNCTION等)"),
        ("AbapStatement", "raw_text", "str", "-", "必須", "生テキスト", "前処理後の元テキスト"),
        ("AbapStatement", "line_number", "int", "0", "-", "行番号", "ソースファイル上の行番号(1始まり)"),
        ("AbapStatement", "tokens", "List[str]", "[]", "-", "トークンリスト", "空白分割されたトークン"),
        ("AbapStatement", "select", "Optional[AbapSelectStatement]", "None", "-", "SELECT情報", "SELECT文の場合のみ詳細情報"),
        ("AbapStatement", "function_call", "Optional[AbapFunctionCall]", "None", "-", "FM呼出情報", "CALL FUNCTION文の場合のみ詳細情報"),
        ("AbapStatement", "data_decl", "Optional[AbapDataDeclaration]", "None", "-", "DATA宣言情報", "DATA文の場合のみ詳細情報"),

        # AbapSelectStatement
        ("AbapSelectStatement", "target_fields", "List[str]", "[]", "-", "選択フィールド", "SELECT句のフィールドリスト"),
        ("AbapSelectStatement", "from_tables", "List[str]", "[]", "-", "FROMテーブル", "FROM句のテーブル名リスト"),
        ("AbapSelectStatement", "where_clause", "str", '""', "-", "WHERE句", "WHERE条件テキスト"),
        ("AbapSelectStatement", "into_clause", "str", '""', "-", "INTO句", "INTO句テキスト"),
        ("AbapSelectStatement", "is_single", "bool", "False", "-", "SINGLE指定", "SELECT SINGLE の場合True"),
        ("AbapSelectStatement", "uses_endselect", "bool", "False", "-", "ENDSELECT使用", "SELECT...ENDSELECTループの場合True"),
        ("AbapSelectStatement", "is_exec_sql", "bool", "False", "-", "EXEC SQL内", "EXEC SQLブロック内のSELECTの場合True"),
        ("AbapSelectStatement", "join_tables", "List[str]", "[]", "-", "JOINテーブル", "INNER/LEFT/RIGHT JOINのテーブル名"),

        # AbapFunctionCall
        ("AbapFunctionCall", "function_name", "str", "-", "必須", "汎用モジュール名", "CALL FUNCTIONで指定された名前"),
        ("AbapFunctionCall", "exporting", "Dict[str, str]", "{}", "-", "EXPORTINGパラメータ", "エクスポートパラメータ名→値"),
        ("AbapFunctionCall", "importing", "Dict[str, str]", "{}", "-", "IMPORTINGパラメータ", "インポートパラメータ名→値"),
        ("AbapFunctionCall", "tables", "Dict[str, str]", "{}", "-", "TABLESパラメータ", "テーブルパラメータ名→値"),
        ("AbapFunctionCall", "exceptions", "Dict[str, str]", "{}", "-", "EXCEPTIONSパラメータ", "例外パラメータ名→値"),
        ("AbapFunctionCall", "is_bapi", "bool", "False", "-", "BAPI判定", "BAPI_で始まる場合True"),

        # AbapDataDeclaration
        ("AbapDataDeclaration", "name", "str", "-", "必須", "変数名", "DATA宣言の変数名"),
        ("AbapDataDeclaration", "type_ref", "str", '""', "-", "TYPE参照", "TYPE句で指定された型名"),
        ("AbapDataDeclaration", "like_ref", "str", '""', "-", "LIKE参照", "LIKE句で指定された参照先"),
        ("AbapDataDeclaration", "value", "Optional[str]", "None", "-", "初期値", "VALUE句で指定された初期値"),
        ("AbapDataDeclaration", "is_table", "bool", "False", "-", "テーブル型", "内部テーブル型の場合True"),

        # MigrationOptions
        ("MigrationOptions", "source_version", "str", '"ECC 6.08"', "-", "移行元バージョン", "ECC 6.0~6.08"),
        ("MigrationOptions", "target_version", "str", '"S/4HANA 2023"', "-", "移行先バージョン", "S/4HANA 1709~2023"),
        ("MigrationOptions", "sap_modules", "List[str]", '["ALL"]', "-", "SAPモジュールフィルタ", "ALL/FI/CO/MM/SD/BP/PP/ABAP"),
        ("MigrationOptions", "encoding", "str", '"utf-8"', "-", "ファイルエンコーディング", "ソースファイルの文字コード"),
        ("MigrationOptions", "extensions", "List[str]", '[".abap",".txt",".prog"]', "-", "対象拡張子", "処理対象のファイル拡張子"),
        ("MigrationOptions", "modernize_syntax", "bool", "True", "-", "構文モダナイズ", "MOVE/COMPUTE等の廃止構文変換"),
        ("MigrationOptions", "convert_tables", "bool", "True", "-", "テーブル変換", "BSEG→ACDOCA等のテーブル名変換"),
        ("MigrationOptions", "convert_bapis", "bool", "True", "-", "BAPI変換", "廃止BAPIの後継BAPI/クラスメソッドへの変換"),
        ("MigrationOptions", "convert_fm", "bool", "True", "-", "FM変換", "廃止汎用モジュールの後継への変換"),
        ("MigrationOptions", "generate_report", "bool", "True", "-", "レポート生成", "HTML/CSVレポートの生成有無"),
        ("MigrationOptions", "add_comments", "bool", "True", "-", "コメント付加", "変換箇所へのマイグレーションコメント"),
        ("MigrationOptions", "backup_originals", "bool", "True", "-", "バックアップ", "オリジナルファイルのバックアップ有無"),
        ("MigrationOptions", "report_format", "str", '"Both"', "-", "レポート形式", "HTML/CSV/Both"),

        # TransformResult
        ("TransformResult", "original_program", "Optional[AbapProgram]", "None", "-", "元プログラム", "変換前のAbapProgram AST"),
        ("TransformResult", "transformed_lines", "List[Tuple[str, int]]", "[]", "-", "変換済み行", "(変換後テキスト, 行番号)のリスト"),
        ("TransformResult", "changes", "List[ChangeRecord]", "[]", "-", "変更記録", "全変更のChangeRecordリスト"),
        ("TransformResult", "auto_converted", "int", "0", "-", "自動変換数", "AUTO深刻度の変更数"),
        ("TransformResult", "needs_review", "int", "0", "-", "レビュー必要数", "REVIEW深刻度の変更数"),
        ("TransformResult", "manual_only", "int", "0", "-", "手動変換数", "MANUAL深刻度の変更数"),

        # ChangeRecord
        ("ChangeRecord", "file", "str", '""', "-", "ファイル名", "変更対象ソースファイル"),
        ("ChangeRecord", "line_number", "int", "0", "-", "行番号", "変更対象行番号"),
        ("ChangeRecord", "category", "str", '""', "-", "カテゴリ", "TABLE/FUNCTION_MODULE/BAPI/SYNTAX/SQL/SELECT_REWRITE"),
        ("ChangeRecord", "sap_module", "str", '""', "-", "SAPモジュール", "FI/CO/MM/SD/BP/PP/ABAP/CROSS"),
        ("ChangeRecord", "severity", "str", '""', "-", "深刻度", "AUTO/REVIEW/MANUAL"),
        ("ChangeRecord", "old_value", "str", '""', "-", "変換前", "変換前の値・パターン"),
        ("ChangeRecord", "new_value", "str", '""', "-", "変換後", "変換後の値・パターン"),
        ("ChangeRecord", "rule_id", "str", '""', "-", "ルールID", "適用されたSimplificationRuleのID"),
        ("ChangeRecord", "description", "str", '""', "-", "説明(EN)", "英語での変更理由・説明"),
        ("ChangeRecord", "description_ja", "str", '""', "-", "説明(JA)", "日本語での変更理由・説明"),

        # SimplificationRule
        ("SimplificationRule", "rule_id", "str", "-", "PK", "ルールID", "一意のルール識別子(例: TABLE_FI_001)"),
        ("SimplificationRule", "category", "str", "-", "必須", "カテゴリ", "TABLE/FUNCTION_MODULE/BAPI/SYNTAX/SQL/SELECT_REWRITE"),
        ("SimplificationRule", "sap_module", "str", "-", "必須", "SAPモジュール", "FI/CO/MM/SD/BP/PP/CROSS/ABAP"),
        ("SimplificationRule", "severity", "str", "-", "必須", "深刻度", "AUTO/REVIEW/MANUAL"),
        ("SimplificationRule", "old_pattern", "str", "-", "必須", "旧パターン", "マッチングパターン(テーブル名/FM名等)"),
        ("SimplificationRule", "new_pattern", "str", "-", "必須", "新パターン", "置換先パターン"),
        ("SimplificationRule", "description", "str", "-", "必須", "説明(EN)", "英語での詳細説明"),
        ("SimplificationRule", "description_ja", "str", "-", "必須", "説明(JA)", "日本語での詳細説明"),
        ("SimplificationRule", "field_mapping", "Dict[str, str]", "{}", "-", "フィールドマッピング", "旧→新フィールド名対応辞書"),
        ("SimplificationRule", "auto_fix", "bool", "True", "-", "自動修正可否", "Trueの場合はツールが自動修正"),
        ("SimplificationRule", "notes", "str", '""', "-", "備考", "追加の注意事項・補足"),

        # IncludeResolution
        ("IncludeResolution", "include_name", "str", "-", "必須", "INCLUDE名", "INCLUDE文で指定されたプログラム名"),
        ("IncludeResolution", "resolved_path", "str", '""', "-", "解決パス", "実ファイルの絶対パス"),
        ("IncludeResolution", "found", "bool", "False", "-", "検出結果", "ファイルが見つかった場合True"),
        ("IncludeResolution", "data_declarations", "List[AbapDataDeclaration]", "[]", "-", "DATA宣言", "INCLUDE内のDATA宣言"),
        ("IncludeResolution", "tables_used", "set", "set()", "-", "使用テーブル", "INCLUDE内で使用されたテーブル"),
        ("IncludeResolution", "nested_includes", "List[str]", "[]", "-", "ネストINCLUDE", "INCLUDE内のさらなるINCLUDE"),
        ("IncludeResolution", "line_count", "int", "0", "-", "行数", "INCLUDEファイルの行数"),
        ("IncludeResolution", "error", "str", '""', "-", "エラー", "解決失敗時のエラーメッセージ"),
    ]

    for i, tbl in enumerate(tables):
        r = row + 1 + i
        for c, val in enumerate(tbl, 1):
            apply_body_cell(ws, r, c, val, wrap=(c >= 6))
        ws.row_dimensions[r].height = 22

    set_col_widths(ws, [22, 24, 30, 26, 12, 20, 42])
    ws.freeze_panes = "A4"


# ============================================================
# Sheet 4: エラー・ログ定義書
# ============================================================
def create_error_log_spec(wb):
    ws = wb.create_sheet("4_エラー・ログ定義書")

    headers = ["エラー/ログID", "区分", "出力レベル", "出力元モジュール",
               "出力タイミング", "メッセージ内容(EN)", "メッセージ内容(JA)", "対処方法"]
    col_count = len(headers)
    add_title_row(ws, "エラー・ログ定義書（詳細設計）", col_count)

    row = 3
    for c, h in enumerate(headers, 1):
        ws.cell(row=row, column=c, value=h)
    apply_header_row(ws, row, col_count)

    entries = [
        ("LOG-P001", "ログ", "INFO", "abap_parser.py",
         "パースファイル開始時", "Parsing file: {filepath}", "ファイル解析中: {filepath}",
         "正常動作ログ。対処不要。"),
        ("LOG-P002", "ログ", "INFO", "abap_parser.py",
         "INCLUDE解決成功時", "Include resolved: {name} -> {path}", "INCLUDE解決: {name} -> {path}",
         "正常動作ログ。"),
        ("ERR-P001", "エラー", "WARNING", "abap_parser.py",
         "INCLUDEファイル未検出時", "Include file not found: {name}", "INCLUDEファイルが見つかりません: {name}",
         "同一ディレクトリまたはサブディレクトリにINCLUDEファイルを配置する。拡張子(.abap/.txt/.prog)を確認。"),
        ("ERR-P002", "エラー", "WARNING", "abap_parser.py",
         "INCLUDE解析失敗時", "Error parsing include: {error}", "INCLUDE解析エラー: {error}",
         "INCLUDEファイルの文字コード・構文を確認する。"),
        ("ERR-P003", "エラー", "WARNING", "abap_parser.py",
         "INCLUDE再帰深度上限到達時", "(max_include_depth exceeded)", "(INCLUDE再帰深度上限超過)",
         "デフォルト上限5。循環INCLUDEの疑いを確認。"),
        ("LOG-T001", "ログ", "INFO", "s4_transformer.py",
         "テーブル変換適用時", "[TABLE] {old} -> {new}", "[テーブル] {old} -> {new}",
         "正常動作。変換結果をレビュー推奨。"),
        ("LOG-T002", "ログ", "INFO", "s4_transformer.py",
         "FM変換適用時", "[FUNCTION_MODULE] {old} -> {new}", "[汎用モジュール] {old} -> {new}",
         "正常動作。パラメータの互換性を要確認。"),
        ("LOG-T003", "ログ", "INFO", "s4_transformer.py",
         "BAPI変換適用時", "[BAPI] {old} -> {new}", "[BAPI] {old} -> {new}",
         "正常動作。後継APIのパラメータ仕様を確認。"),
        ("LOG-T004", "ログ", "INFO", "s4_transformer.py",
         "構文モダナイズ適用時", "[SYNTAX] {old} -> {new}", "[構文] {old} -> {new}",
         "正常動作。自動変換(AUTO)で対処不要。"),
        ("LOG-T005", "ログ", "WARNING", "s4_transformer.py",
         "EXEC SQL検出時", "[MANUAL] EXEC SQL...ENDEXEC detected", "[手動] EXEC SQL...ENDEXEC を検出",
         "Open SQLまたはABAP SQLへの手動変換が必要。EXEC SQLはS/4HANAでも動作するが非推奨。"),
        ("LOG-T006", "ログ", "INFO", "s4_transformer.py",
         "SELECT書換ルール適用時", "[SELECT_REWRITE] JOIN simplification", "[SELECT書換] JOIN簡素化",
         "JOINが不要になるテーブル統合。フィールドマッピングをレビュー。"),
        ("LOG-G001", "ログ", "INFO", "abap_generator.py",
         "ファイル出力時", "Generated: {output_path}", "生成完了: {output_path}",
         "正常動作。"),
        ("LOG-G002", "ログ", "INFO", "abap_generator.py",
         "バックアップ作成時", "Backup created: {backup_path}", "バックアップ作成: {backup_path}",
         "正常動作。"),
        ("LOG-R001", "ログ", "INFO", "report_generator.py",
         "HTMLレポート生成時", "HTML report generated: {path}", "HTMLレポート生成: {path}",
         "正常動作。"),
        ("LOG-R002", "ログ", "INFO", "report_generator.py",
         "CSVレポート生成時", "CSV report generated: {path}", "CSVレポート生成: {path}",
         "正常動作。"),
        ("LOG-M001", "ログ", "INFO/header", "main.py (GUI)",
         "変換開始時", "Starting migration...", "マイグレーション開始...",
         "GUIログ領域に表示。"),
        ("ERR-M001", "エラー", "WARNING", "main.py (GUI)",
         "入力フォルダ未指定時", "Please select input folder", "入力フォルダを選択してください",
         "GUIダイアログ。入力フォルダを指定する。"),
        ("ERR-M002", "エラー", "WARNING", "main.py (GUI)",
         "出力フォルダ未指定時", "Please select output folder", "出力フォルダを選択してください",
         "GUIダイアログ。出力フォルダを指定する。"),
        ("ERR-M003", "エラー", "ERROR", "main.py (GUI)",
         "入力フォルダ不存在時", "Input directory does not exist: {path}", "入力ディレクトリが存在しません: {path}",
         "有効なディレクトリパスを指定する。"),
        ("ERR-M004", "エラー", "WARNING", "main.py (GUI)",
         "対象ファイル0件時", "No ABAP files found with extensions: {ext}", "指定拡張子のABAPファイルが見つかりません: {ext}",
         "拡張子設定を確認。ディレクトリパスを確認。"),
        ("LOG-M002", "ログ", "WARNING", "main.py (GUI)",
         "キャンセル要求時", "Cancellation requested...", "キャンセル要求中...",
         "現在処理中のファイル完了後に停止。"),
        ("ERR-M005", "エラー", "ERROR", "main.py (GUI/CLI)",
         "個別ファイル処理失敗時", "ERROR: {exception message}", "エラー: {例外メッセージ}",
         "スタックトレースとともにログ出力。該当ファイルをスキップし後続処理を継続。"),
        ("ERR-M006", "エラー", "FATAL", "main.py (GUI/CLI)",
         "致命的エラー発生時", "Fatal error: {exception}", "致命的エラー: {例外}",
         "変換処理全体が中断。エラー内容を確認し、環境・入力を修正。"),
        ("SEV-AUTO", "変更通知", "INFO (green)", "s4_transformer.py",
         "自動変換完了時", "[S4-AUTO] {category}: {old} -> {new}", "[S4-AUTO] {category}: {old} -> {new}",
         "自動変換済み。基本的に対処不要だが、動作確認推奨。"),
        ("SEV-REVIEW", "変更通知", "WARNING (yellow)", "s4_transformer.py",
         "レビュー要変換時", "[S4-REVIEW] {category}: {old} -> {new} (PLEASE REVIEW)", "[S4-REVIEW] {category}: {old} -> {new} (レビュー必要)",
         "変換は実施済みだが、フィールドマッピングやビジネスロジックの確認が必要。"),
        ("SEV-MANUAL", "変更通知", "ERROR (red)", "s4_transformer.py",
         "手動変換要求時", "[S4-MANUAL] {category}: MANUAL CONVERSION REQUIRED",
         "[S4-MANUAL] {category}: 手動変換必須",
         "ツールでは自動変換不可。開発者による手動対応が必要。"),
    ]

    for i, entry in enumerate(entries):
        r = row + 1 + i
        for c, val in enumerate(entry, 1):
            apply_body_cell(ws, r, c, val, wrap=True)
        ws.row_dimensions[r].height = 42

    set_col_widths(ws, [14, 10, 16, 20, 22, 42, 42, 42])
    ws.freeze_panes = "A4"


# ============================================================
# Sheet 5: アーキテクチャ図解 (Mermaid)
# ============================================================
def create_architecture_diagrams(wb):
    ws = wb.create_sheet("5_アーキテクチャ図解")

    headers = ["図表ID", "図表名", "Mermaidコード"]
    col_count = len(headers)
    add_title_row(ws, "アーキテクチャ図解（Mermaid記法）", col_count)

    row = 3
    for c, h in enumerate(headers, 1):
        ws.cell(row=row, column=c, value=h)
    apply_header_row(ws, row, col_count)

    diagrams = [
        ("ARCH-001", "システム構成図（全体アーキテクチャ）",
"""graph TB
    subgraph "ユーザーインターフェース"
        GUI["GUI (tkinter) / main.py - AbapToS4App"]
        CLI["CLI モード / main.py - run_cli()"]
    end

    subgraph "コアエンジン"
        PARSER["ABAP Parser / src/abap_parser.py"]
        TRANSFORMER["S/4 Transformer / src/s4_transformer.py"]
        GENERATOR["Code Generator / src/abap_generator.py"]
        REPORTER["Report Generator / src/report_generator.py"]
    end

    subgraph "ルール・マスタデータ"
        RULES["Simplification Rules / src/simplification_rules.py (50+ rules)"]
        VENDOR["Vendor Modules / src/vendor_modules.py (113 tables, 14 field mappings)"]
        I18N["i18n / src/i18n.py (59 languages)"]
    end

    subgraph "入出力"
        INPUT["入力: ABAPソースファイル"]
        OUTPUT_CODE["出力: 変換済みABAPファイル (_s4)"]
        OUTPUT_REPORT["出力: レポート HTML / CSV"]
        OUTPUT_BACKUP["出力: バックアップ (.bak)"]
    end

    GUI --> PARSER
    CLI --> PARSER
    INPUT --> PARSER
    PARSER --> TRANSFORMER
    TRANSFORMER --> GENERATOR
    TRANSFORMER --> REPORTER
    RULES --> TRANSFORMER
    VENDOR --> TRANSFORMER
    I18N --> GUI
    GENERATOR --> OUTPUT_CODE
    GENERATOR --> OUTPUT_BACKUP
    REPORTER --> OUTPUT_REPORT"""),

        ("ARCH-002", "処理シーケンス図（メイン変換フロー）",
"""sequenceDiagram
    actor User as ユーザー
    participant UI as GUI/CLI
    participant Parser as AbapParser
    participant Trans as S4Transformer
    participant Rules as SimplificationRules
    participant Gen as AbapCodeGenerator
    participant Report as ReportGenerator

    User->>UI: 入力/出力フォルダ指定 + オプション設定
    UI->>UI: MigrationOptions構築

    loop 各ABAPファイル
        UI->>Parser: parse_file(filepath)
        Parser->>Parser: 前処理 (コメント除去, 行結合, チェーン展開)
        Parser->>Parser: AST構築 (ステートメント分類)
        Parser->>Parser: INCLUDE解決 (再帰)
        Parser-->>UI: AbapProgram

        UI->>Trans: transform(program, source_file)
        Trans->>Rules: table_mappings / fm_mappings / bapi_mappings
        Trans->>Trans: テーブル変換 -> FM変換 -> BAPI変換
        Trans->>Trans: SELECT書換 -> SQL構文 -> 廃止構文 -> EXEC SQL
        Trans-->>UI: TransformResult

        UI->>Gen: generate(result, output_path)
        Gen-->>UI: .abap ファイル出力

        UI->>Gen: BackupManager.backup_file()
        Gen-->>UI: .bak ファイル出力
    end

    UI->>Report: generate(all_results, report_dir)
    Report->>Report: HTML生成 (ダッシュボード + 詳細)
    Report->>Report: CSV生成
    Report-->>UI: レポートファイル出力
    UI-->>User: 完了通知 + サマリ表示"""),

        ("ARCH-003", "データフロー図（AST変換パイプライン）",
"""graph LR
    A["ABAP Source (.abap/.txt/.prog)"] --> B["前処理: コメント除去, 行結合, チェーン文展開"]
    B --> C["ステートメント分類 (90+ types)"]
    C --> D["AbapProgram AST 生成"]

    D --> E{"変換パイプライン"}

    E --> E1["1. テーブル名変換 (BSEG->ACDOCA, MKPF/MSEG->MATDOC)"]
    E1 --> E2["2. FM変換 (廃止FM->後継FM)"]
    E2 --> E3["3. BAPI変換 (BAPI_VENDOR_*->CL_MD_BP_MAINTAIN)"]
    E3 --> E4["4. SELECT書換 (JOIN簡素化, 単一テーブル化)"]
    E4 --> E5["5. SQL構文 (INTO CORRESPONDING->@DATA())"]
    E5 --> E6["6. 廃止構文 (MOVE->代入, COMPUTE->式)"]
    E6 --> E7["7. EXEC SQL (検出・マーク)"]

    E7 --> F["TransformResult: 変換済み行 + ChangeRecordリスト"]

    F --> G1["変換済みABAPファイル"]
    F --> G2["HTML/CSVレポート"]"""),

        ("ARCH-004", "クラス図（主要データクラス関連）",
"""classDiagram
    class AbapProgram {
        +str report_name
        +str program_type
        +str source_file
        +List includes
        +List data_declarations
        +List select_statements
        +List function_calls
        +List form_routines
        +List statements
        +set tables_used
        +set function_modules_used
        +set bapis_used
        +bool has_exec_sql
        +int total_lines
    }

    class AbapStatement {
        +AbapStatementType type
        +str raw_text
        +int line_number
        +AbapSelectStatement select
        +AbapFunctionCall function_call
        +AbapDataDeclaration data_decl
    }

    class MigrationOptions {
        +str source_version
        +str target_version
        +List sap_modules
        +str encoding
        +bool modernize_syntax
        +bool convert_tables
        +bool convert_bapis
        +bool convert_fm
    }

    class TransformResult {
        +AbapProgram original_program
        +List transformed_lines
        +List changes
        +int auto_converted
        +int needs_review
        +int manual_only
        +add_change(ChangeRecord)
    }

    class ChangeRecord {
        +str file
        +int line_number
        +str category
        +str sap_module
        +str severity
        +str old_value
        +str new_value
        +str rule_id
    }

    class SimplificationRule {
        +str rule_id
        +str category
        +str sap_module
        +str severity
        +str old_pattern
        +str new_pattern
        +Dict field_mapping
        +bool auto_fix
    }

    AbapProgram "1" *-- "n" AbapStatement
    AbapProgram "1" *-- "n" AbapSelectStatement
    AbapProgram "1" *-- "n" AbapFunctionCall
    TransformResult "1" o-- "1" AbapProgram
    TransformResult "1" *-- "n" ChangeRecord
    S4Transformer --> SimplificationRule : uses
    S4Transformer --> AbapProgram : transforms
    S4Transformer --> TransformResult : produces"""),

        ("ARCH-005", "SAPモジュールとテーブル変換のER図",
"""erDiagram
    SAP_MODULE ||--o{ TABLE_MAPPING : has
    SAP_MODULE ||--o{ FM_MAPPING : has
    SAP_MODULE ||--o{ BAPI_MAPPING : has
    TABLE_MAPPING ||--o{ FIELD_MAPPING : contains
    TABLE_MAPPING ||--o{ CDS_VIEW : replaced_by

    SAP_MODULE {
        string module_id PK
        string description
    }

    TABLE_MAPPING {
        string old_table PK
        string new_table
        string sap_module FK
        string severity
    }

    FIELD_MAPPING {
        string old_table FK
        string new_table FK
        string old_field
        string new_field
    }

    FM_MAPPING {
        string old_fm PK
        string new_fm
        string sap_module FK
    }

    BAPI_MAPPING {
        string old_bapi PK
        string new_api
        string sap_module FK
    }

    CDS_VIEW {
        string table_name FK
        string cds_view_name
        string description
    }"""),

        ("ARCH-006", "GUI画面構成図",
"""graph TB
    subgraph "メインウィンドウ (900x800)"
        TOP["タイトルバー + 言語セレクタ (59言語)"]

        subgraph "フォルダ選択セクション"
            IN["入力フォルダ [Entry] + [参照] ボタン"]
            OUT["出力フォルダ [Entry] + [参照] ボタン"]
        end

        subgraph "オプションセクション (2カラム)"
            LEFT["左カラム: Source Version, Target Version, Encoding, Extensions, Module Filter, Report Format"]
            RIGHT["右カラム: Modernize Syntax, Convert Tables, Convert BAPIs, Convert FMs, Generate Report, Add Comments, Backup Originals"]
        end

        BUTTONS["[変換実行] [キャンセル] ...... [ログクリア]"]
        PROGRESS["プログレスバー + ステータスラベル"]
        LOG["ログ出力エリア (ScrolledText) Consolas 9pt ダークテーマ 色分け: info=緑, success=暗緑, warning=黄, error=赤, header=青"]
    end

    TOP --> IN
    IN --> OUT
    OUT --> LEFT
    LEFT --> RIGHT
    RIGHT --> BUTTONS
    BUTTONS --> PROGRESS
    PROGRESS --> LOG"""),
    ]

    for i, (diag_id, diag_name, mermaid_code) in enumerate(diagrams):
        r = row + 1 + i
        apply_body_cell(ws, r, 1, diag_id)
        apply_body_cell(ws, r, 2, diag_name, wrap=True)
        apply_body_cell(ws, r, 3, mermaid_code, wrap=True)
        ws.row_dimensions[r].height = 400

    set_col_widths(ws, [14, 30, 120])
    ws.freeze_panes = "A4"


# ============================================================
# メイン実行
# ============================================================
def main():
    print("設計書生成を開始します...")

    wb = Workbook()

    print("  [1/5] 機能一覧表...")
    create_feature_list(wb)

    print("  [2/5] API仕様書...")
    create_api_spec(wb)

    print("  [3/5] テーブル定義書...")
    create_table_definitions(wb)

    print("  [4/5] エラー・ログ定義書...")
    create_error_log_spec(wb)

    print("  [5/5] アーキテクチャ図解...")
    create_architecture_diagrams(wb)

    wb.save(OUTPUT_PATH)
    print(f"\n設計書を生成しました: {OUTPUT_PATH}")
    print(f"  シート数: {len(wb.sheetnames)}")
    for name in wb.sheetnames:
        print(f"    - {name}")


if __name__ == "__main__":
    main()
