"""
SAP ECC to S/4HANA Simplification Rules
========================================
Contains the SAP Simplification List rules as Python data structures.
Each rule describes a change needed when migrating from ECC to S/4HANA.

Based on SAP Simplification List for S/4HANA 2023.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class SimplificationRule:
    """Represents a single simplification rule for ECC to S/4HANA migration."""

    rule_id: str                    # e.g. "TABLE_FI_001"
    category: str                   # "TABLE", "FUNCTION_MODULE", "BAPI", "SYNTAX", "SQL", "TRANSACTION"
    sap_module: str                 # "FI", "CO", "MM", "SD", "BP", "PP", "CROSS", "ABAP"
    severity: str                   # "AUTO", "REVIEW", "MANUAL"
    old_pattern: str                # What to match
    new_pattern: str                # Replacement (or description if MANUAL)
    description: str                # Human-readable explanation
    description_ja: str             # Japanese description
    field_mapping: Dict[str, str] = field(default_factory=dict)
    auto_fix: bool = True
    notes: str = ""


class SimplificationRules:
    """
    Registry of all SAP Simplification List rules for ECC to S/4HANA migration.

    Rules are categorized by type (TABLE, FUNCTION_MODULE, BAPI, SYNTAX, SQL)
    and SAP module (FI, CO, MM, SD, BP, ABAP, CROSS).

    Severity levels:
        AUTO   - Tool can fix automatically
        REVIEW - Tool fixes but needs human verification
        MANUAL - Cannot be auto-fixed, requires manual intervention
    """

    def __init__(self, source_version: str = "ECC 6.08", target_version: str = "S/4HANA 2023"):
        self.source_version = source_version
        self.target_version = target_version
        self._rules: List[SimplificationRule] = []
        self._init_all_rules()

    @property
    def table_mappings(self) -> Dict[str, SimplificationRule]:
        """Get table name -> rule mapping for all TABLE category rules."""
        return {
            rule.old_pattern: rule
            for rule in self._rules
            if rule.category == "TABLE"
        }

    @property
    def fm_mappings(self) -> Dict[str, SimplificationRule]:
        """Get function module name -> rule mapping."""
        return {
            rule.old_pattern: rule
            for rule in self._rules
            if rule.category == "FUNCTION_MODULE"
        }

    @property
    def bapi_mappings(self) -> Dict[str, SimplificationRule]:
        """Get BAPI name -> rule mapping."""
        return {
            rule.old_pattern: rule
            for rule in self._rules
            if rule.category == "BAPI"
        }

    @property
    def syntax_rules(self) -> List[SimplificationRule]:
        """Get syntax modernization rules."""
        return [rule for rule in self._rules if rule.category == "SYNTAX"]

    @property
    def sql_rules(self) -> List[SimplificationRule]:
        """Get SQL migration rules."""
        return [rule for rule in self._rules if rule.category == "SQL"]

    @property
    def cross_module_rules(self) -> List[SimplificationRule]:
        """Get cross-module rules."""
        return [rule for rule in self._rules if rule.sap_module == "CROSS"]

    def get_rules_by_module(self, module: str) -> List[SimplificationRule]:
        """Filter rules by SAP module (FI, CO, MM, SD, BP, ABAP, CROSS)."""
        return [rule for rule in self._rules if rule.sap_module == module.upper()]

    def get_rules_by_category(self, category: str) -> List[SimplificationRule]:
        """Filter rules by category (TABLE, FUNCTION_MODULE, BAPI, SYNTAX, SQL)."""
        return [rule for rule in self._rules if rule.category == category.upper()]

    def get_rules_by_severity(self, severity: str) -> List[SimplificationRule]:
        """Filter rules by severity (AUTO, REVIEW, MANUAL)."""
        return [rule for rule in self._rules if rule.severity == severity.upper()]

    def get_rule_by_id(self, rule_id: str) -> Optional[SimplificationRule]:
        """Look up a single rule by its ID."""
        for rule in self._rules:
            if rule.rule_id == rule_id:
                return rule
        return None

    def get_all_rules(self) -> List[SimplificationRule]:
        """Return all rules."""
        return list(self._rules)

    def get_auto_fixable_rules(self) -> List[SimplificationRule]:
        """Return only rules that can be auto-fixed."""
        return [rule for rule in self._rules if rule.auto_fix and rule.severity == "AUTO"]

    def __len__(self) -> int:
        return len(self._rules)

    def __iter__(self):
        return iter(self._rules)

    # ----------------------------------------------------------------
    # Rule initialization methods
    # ----------------------------------------------------------------

    def _init_all_rules(self):
        """Initialize all simplification rules."""
        self._init_fi_co_rules()
        self._init_mm_rules()
        self._init_sd_rules()
        self._init_bp_rules()
        self._init_abap_syntax_rules()
        self._init_sql_rules()
        self._init_fm_rules()
        self._init_cross_module_rules()

    # ----------------------------------------------------------------
    # FI/CO Table Rules
    # ----------------------------------------------------------------

    def _init_fi_co_rules(self):
        """Initialize FI/CO table migration rules (16 rules)."""

        # Common BSEG -> ACDOCA field mapping
        bseg_acdoca_mapping = {
            "BUKRS": "RBUKRS",
            "BELNR": "BELNR",
            "GJAHR": "GJAHR",
            "BUZEI": "DOCLN",
            "KOART": "KOART",
            "SHKZG": "DRCRK",
            "DMBTR": "HSL",
            "WRBTR": "TSL",
            "HKONT": "RACCT",
            "KOSTL": "RCNTR",
            "PRCTR": "PRCTR",
            "GSBER": "SEGMENT",
        }

        self._rules.append(SimplificationRule(
            rule_id="TABLE_FI_001",
            category="TABLE",
            sap_module="FI",
            severity="REVIEW",
            old_pattern="BSEG",
            new_pattern="ACDOCA",
            description="Accounting document line items table BSEG is replaced by Universal Journal ACDOCA. "
                        "BSEG becomes a compatibility view in S/4HANA. Direct SELECT on BSEG cluster table "
                        "must be migrated to ACDOCA with field mapping changes.",
            description_ja="会計伝票明細テーブルBSEGはユニバーサルジャーナルACDOCAに置き換えられます。"
                           "S/4HANAではBSEGは互換性ビューとなります。BSEGクラスタテーブルへの直接SELECTは"
                           "フィールドマッピング変更を伴いACDOCAに移行する必要があります。",
            field_mapping=bseg_acdoca_mapping,
            auto_fix=False,
            notes="BSEG is a cluster table in ECC; ACDOCA is a transparent table. "
                  "Performance characteristics change significantly.",
        ))

        self._rules.append(SimplificationRule(
            rule_id="TABLE_FI_002",
            category="TABLE",
            sap_module="FI",
            severity="REVIEW",
            old_pattern="BKPF",
            new_pattern="ACDOCA",
            description="Accounting document header table BKPF still exists in S/4HANA but header data "
                        "is also available in ACDOCA. Consider consolidating header+item queries to ACDOCA.",
            description_ja="会計伝票ヘッダテーブルBKPFはS/4HANAでも存在しますが、ヘッダデータは"
                           "ACDOCAでも利用可能です。ヘッダ+明細のクエリをACDOCAに統合することを検討してください。",
            field_mapping={"BUKRS": "RBUKRS", "BELNR": "BELNR", "GJAHR": "GJAHR",
                           "BLART": "BLART", "BUDAT": "BUDAT", "BLDAT": "BLDAT"},
            auto_fix=False,
            notes="BKPF remains available but ACDOCA is the single source of truth.",
        ))

        self._rules.append(SimplificationRule(
            rule_id="TABLE_FI_003",
            category="TABLE",
            sap_module="FI",
            severity="REVIEW",
            old_pattern="BSIS",
            new_pattern="ACDOCA",
            description="GL account open items (BSIS) are replaced by ACDOCA. "
                        "Filter on AUGDT (clearing date) IS INITIAL for open items.",
            description_ja="GL勘定未消込明細(BSIS)はACDOCAに置き換えられます。"
                           "未消込明細にはAUGDT(消込日付)がINITIALの条件でフィルタしてください。",
            field_mapping={"BUKRS": "RBUKRS", "HKONT": "RACCT", "BELNR": "BELNR",
                           "GJAHR": "GJAHR", "DMBTR": "HSL", "WRBTR": "TSL"},
            auto_fix=False,
            notes="Open item determination changes: use AUGDT IS INITIAL in ACDOCA.",
        ))

        self._rules.append(SimplificationRule(
            rule_id="TABLE_FI_004",
            category="TABLE",
            sap_module="FI",
            severity="REVIEW",
            old_pattern="BSAS",
            new_pattern="ACDOCA",
            description="GL account cleared items (BSAS) are replaced by ACDOCA. "
                        "Filter on AUGDT (clearing date) IS NOT INITIAL for cleared items.",
            description_ja="GL勘定消込済明細(BSAS)はACDOCAに置き換えられます。"
                           "消込済明細にはAUGDTがNOT INITIALの条件でフィルタしてください。",
            field_mapping={"BUKRS": "RBUKRS", "HKONT": "RACCT", "BELNR": "BELNR",
                           "GJAHR": "GJAHR", "DMBTR": "HSL", "WRBTR": "TSL"},
            auto_fix=False,
            notes="Cleared item determination: use AUGDT IS NOT INITIAL in ACDOCA.",
        ))

        self._rules.append(SimplificationRule(
            rule_id="TABLE_FI_005",
            category="TABLE",
            sap_module="FI",
            severity="REVIEW",
            old_pattern="BSID",
            new_pattern="ACDOCA",
            description="Customer open items (BSID) are replaced by ACDOCA. "
                        "Filter on KOART = 'D' and AUGDT IS INITIAL.",
            description_ja="得意先未消込明細(BSID)はACDOCAに置き換えられます。"
                           "KOART = 'D' かつ AUGDT IS INITIALでフィルタしてください。",
            field_mapping={"BUKRS": "RBUKRS", "KUNNR": "KUNNR", "BELNR": "BELNR",
                           "GJAHR": "GJAHR", "DMBTR": "HSL", "WRBTR": "TSL"},
            auto_fix=False,
            notes="Customer subledger items now in ACDOCA with KOART = 'D'.",
        ))

        self._rules.append(SimplificationRule(
            rule_id="TABLE_FI_006",
            category="TABLE",
            sap_module="FI",
            severity="REVIEW",
            old_pattern="BSAD",
            new_pattern="ACDOCA",
            description="Customer cleared items (BSAD) are replaced by ACDOCA. "
                        "Filter on KOART = 'D' and AUGDT IS NOT INITIAL.",
            description_ja="得意先消込済明細(BSAD)はACDOCAに置き換えられます。"
                           "KOART = 'D' かつ AUGDT IS NOT INITIALでフィルタしてください。",
            field_mapping={"BUKRS": "RBUKRS", "KUNNR": "KUNNR", "BELNR": "BELNR",
                           "GJAHR": "GJAHR", "DMBTR": "HSL", "WRBTR": "TSL"},
            auto_fix=False,
            notes="Customer cleared items: KOART = 'D' and AUGDT IS NOT INITIAL.",
        ))

        self._rules.append(SimplificationRule(
            rule_id="TABLE_FI_007",
            category="TABLE",
            sap_module="FI",
            severity="REVIEW",
            old_pattern="BSIK",
            new_pattern="ACDOCA",
            description="Vendor open items (BSIK) are replaced by ACDOCA. "
                        "Filter on KOART = 'K' and AUGDT IS INITIAL.",
            description_ja="仕入先未消込明細(BSIK)はACDOCAに置き換えられます。"
                           "KOART = 'K' かつ AUGDT IS INITIALでフィルタしてください。",
            field_mapping={"BUKRS": "RBUKRS", "LIFNR": "LIFNR", "BELNR": "BELNR",
                           "GJAHR": "GJAHR", "DMBTR": "HSL", "WRBTR": "TSL"},
            auto_fix=False,
            notes="Vendor subledger items now in ACDOCA with KOART = 'K'.",
        ))

        self._rules.append(SimplificationRule(
            rule_id="TABLE_FI_008",
            category="TABLE",
            sap_module="FI",
            severity="REVIEW",
            old_pattern="BSAK",
            new_pattern="ACDOCA",
            description="Vendor cleared items (BSAK) are replaced by ACDOCA. "
                        "Filter on KOART = 'K' and AUGDT IS NOT INITIAL.",
            description_ja="仕入先消込済明細(BSAK)はACDOCAに置き換えられます。"
                           "KOART = 'K' かつ AUGDT IS NOT INITIALでフィルタしてください。",
            field_mapping={"BUKRS": "RBUKRS", "LIFNR": "LIFNR", "BELNR": "BELNR",
                           "GJAHR": "GJAHR", "DMBTR": "HSL", "WRBTR": "TSL"},
            auto_fix=False,
            notes="Vendor cleared items: KOART = 'K' and AUGDT IS NOT INITIAL.",
        ))

        self._rules.append(SimplificationRule(
            rule_id="TABLE_FI_009",
            category="TABLE",
            sap_module="FI",
            severity="REVIEW",
            old_pattern="GLT0",
            new_pattern="ACDOCA",
            description="GL account totals table GLT0 is replaced by ACDOCA aggregation. "
                        "Totals are computed on-the-fly from ACDOCA line items in S/4HANA.",
            description_ja="GL勘定合計テーブルGLT0はACDOCA集計に置き換えられます。"
                           "S/4HANAでは合計はACDOCA明細からリアルタイムに計算されます。",
            field_mapping={"BUKRS": "RBUKRS", "RACCT": "RACCT", "GJAHR": "GJAHR",
                           "HSLxx": "HSL (aggregate)", "TSLxx": "TSL (aggregate)"},
            auto_fix=False,
            notes="Period-based totals (HSL01-HSL16) replaced by SUM aggregation on ACDOCA.",
        ))

        self._rules.append(SimplificationRule(
            rule_id="TABLE_FI_010",
            category="TABLE",
            sap_module="FI",
            severity="AUTO",
            old_pattern="FAGLFLEXA",
            new_pattern="ACDOCA",
            description="New GL line items table FAGLFLEXA is replaced by ACDOCA. "
                        "This is a straightforward replacement with similar field structure.",
            description_ja="新GL明細テーブルFAGLFLEXAはACDOCAに置き換えられます。"
                           "類似のフィールド構造による直接的な置換です。",
            field_mapping={"RBUKRS": "RBUKRS", "BELNR": "BELNR", "GJAHR": "GJAHR",
                           "DOCLN": "DOCLN", "RACCT": "RACCT", "HSL": "HSL", "TSL": "TSL",
                           "RCNTR": "RCNTR", "PRCTR": "PRCTR"},
            auto_fix=True,
            notes="FAGLFLEXA and ACDOCA share most field names. Simplest migration path.",
        ))

        self._rules.append(SimplificationRule(
            rule_id="TABLE_FI_011",
            category="TABLE",
            sap_module="FI",
            severity="REVIEW",
            old_pattern="FAGLFLEXT",
            new_pattern="ACDOCA",
            description="New GL totals table FAGLFLEXT is replaced by ACDOCA aggregation. "
                        "Period totals are computed from ACDOCA line items.",
            description_ja="新GL合計テーブルFAGLFLEXTはACDOCA集計に置き換えられます。"
                           "期間合計はACDOCA明細から計算されます。",
            field_mapping={"RBUKRS": "RBUKRS", "RACCT": "RACCT", "GJAHR": "GJAHR",
                           "HSLxx": "HSL (aggregate)", "TSLxx": "TSL (aggregate)"},
            auto_fix=False,
            notes="Similar to GLT0 migration. Period columns replaced by aggregation.",
        ))

        # CO tables
        self._rules.append(SimplificationRule(
            rule_id="TABLE_FI_012",
            category="TABLE",
            sap_module="CO",
            severity="REVIEW",
            old_pattern="COSS",
            new_pattern="ACDOCA",
            description="CO internal postings (COSS) are merged into ACDOCA. "
                        "CO line items are now part of the Universal Journal.",
            description_ja="CO内部転記(COSS)はACDOCAに統合されます。"
                           "CO明細はユニバーサルジャーナルの一部となります。",
            field_mapping={"OBJNR": "OBJNR", "GJAHR": "GJAHR", "KSTAR": "RACCT",
                           "WKG001": "HSL (per period)", "WOG001": "TSL (per period)"},
            auto_fix=False,
            notes="CO statistical key figures and allocation data require special handling.",
        ))

        self._rules.append(SimplificationRule(
            rule_id="TABLE_FI_013",
            category="TABLE",
            sap_module="CO",
            severity="REVIEW",
            old_pattern="COSP",
            new_pattern="ACDOCA",
            description="CO external postings (COSP) are merged into ACDOCA. "
                        "Primary cost postings from FI are directly in ACDOCA.",
            description_ja="CO外部転記(COSP)はACDOCAに統合されます。"
                           "FIからの一次原価転記はACDOCAに直接含まれます。",
            field_mapping={"OBJNR": "OBJNR", "GJAHR": "GJAHR", "KSTAR": "RACCT",
                           "WKG001": "HSL (per period)", "WOG001": "TSL (per period)"},
            auto_fix=False,
            notes="Period-based amount fields (WKG001-WKG016) are replaced by line items.",
        ))

        self._rules.append(SimplificationRule(
            rule_id="TABLE_FI_014",
            category="TABLE",
            sap_module="CO",
            severity="REVIEW",
            old_pattern="COBK",
            new_pattern="ACDOCA",
            description="CO document header (COBK) data is available through ACDOCA header fields. "
                        "CO documents are now part of the unified journal entry.",
            description_ja="CO伝票ヘッダ(COBK)データはACDOCAヘッダフィールドを通じて利用可能です。"
                           "CO伝票は統合仕訳の一部となります。",
            field_mapping={"KOKRS": "KOKRS", "BELNR": "BELNR", "GJAHR": "GJAHR",
                           "BLDAT": "BLDAT", "BUDAT": "BUDAT"},
            auto_fix=False,
            notes="CO-specific header fields may need to be retrieved from ACDOCA differently.",
        ))

        self._rules.append(SimplificationRule(
            rule_id="TABLE_FI_015",
            category="TABLE",
            sap_module="FI",
            severity="REVIEW",
            old_pattern="ANLA",
            new_pattern="ACDOCA",
            description="Asset master records (ANLA) remain in S/4HANA but asset value postings "
                        "are reflected in ACDOCA. Asset reporting may need to reference both.",
            description_ja="資産マスタレコード(ANLA)はS/4HANAでも残りますが、資産価額転記は"
                           "ACDOCAに反映されます。資産レポートは両方を参照する必要がある場合があります。",
            field_mapping={"BUKRS": "RBUKRS", "ANLN1": "ANLN1", "ANLN2": "ANLN2"},
            auto_fix=False,
            notes="ANLA master data stays; transactional data moves to ACDOCA. Partial migration.",
        ))

        self._rules.append(SimplificationRule(
            rule_id="TABLE_FI_016",
            category="TABLE",
            sap_module="FI",
            severity="REVIEW",
            old_pattern="ANLC",
            new_pattern="ACDOCA",
            description="Asset value fields (ANLC) are replaced by ACDOCA for transaction-level data. "
                        "Cumulative asset values can be derived from ACDOCA aggregation.",
            description_ja="資産価額フィールド(ANLC)はトランザクションレベルのデータについてACDOCAに"
                           "置き換えられます。累計資産価額はACDOCA集計から導出可能です。",
            field_mapping={"BUKRS": "RBUKRS", "ANLN1": "ANLN1", "ANLN2": "ANLN2",
                           "GJAHR": "GJAHR", "AFABE": "AFABE"},
            auto_fix=False,
            notes="Asset depreciation area values (ANLC) move to ACDOCA line items.",
        ))

    # ----------------------------------------------------------------
    # MM Table Rules
    # ----------------------------------------------------------------

    def _init_mm_rules(self):
        """Initialize MM table migration rules (4 rules)."""

        mkpf_matdoc_mapping = {
            "MBLNR": "MBLNR",
            "MJAHR": "MJAHR",
            "BUDAT": "BUDAT_MKPF",
            "BLDAT": "BLDAT",
            "USNAM": "USNAM",
            "BWART": "BWART",
            "XBLNR": "XBLNR",
        }

        mseg_matdoc_mapping = {
            "MBLNR": "MBLNR",
            "MJAHR": "MJAHR",
            "ZEILE": "MBLPO",
            "BWART": "BWART",
            "MATNR": "MATNR",
            "WERKS": "WERKS",
            "LGORT": "LGORT",
            "MENGE": "ERFMG",
            "MEINS": "ERFME",
            "DMBTR": "DMBTR_STOCK",
            "EBELN": "EBELN",
            "EBELP": "EBELP",
            "LIFNR": "LIFNR",
        }

        self._rules.append(SimplificationRule(
            rule_id="TABLE_MM_001",
            category="TABLE",
            sap_module="MM",
            severity="AUTO",
            old_pattern="MKPF",
            new_pattern="MATDOC",
            description="Material document header (MKPF) is merged into MATDOC. "
                        "Header and item data are combined in a single table.",
            description_ja="入出庫伝票ヘッダ(MKPF)はMATDOCに統合されます。"
                           "ヘッダと明細データが単一テーブルに統合されます。",
            field_mapping=mkpf_matdoc_mapping,
            auto_fix=True,
            notes="MATDOC combines MKPF+MSEG. Header fields available at item level.",
        ))

        self._rules.append(SimplificationRule(
            rule_id="TABLE_MM_002",
            category="TABLE",
            sap_module="MM",
            severity="AUTO",
            old_pattern="MSEG",
            new_pattern="MATDOC",
            description="Material document items (MSEG) are merged into MATDOC. "
                        "MSEG becomes a compatibility view in S/4HANA.",
            description_ja="入出庫伝票明細(MSEG)はMATDOCに統合されます。"
                           "MSEGはS/4HANAでは互換性ビューとなります。",
            field_mapping=mseg_matdoc_mapping,
            auto_fix=True,
            notes="MSEG cluster table replaced by transparent table MATDOC.",
        ))

        self._rules.append(SimplificationRule(
            rule_id="TABLE_MM_003",
            category="TABLE",
            sap_module="MM",
            severity="REVIEW",
            old_pattern="ISEG",
            new_pattern="MATDOC",
            description="Physical inventory document items (ISEG) are incorporated into MATDOC. "
                        "Physical inventory processes are restructured in S/4HANA.",
            description_ja="棚卸伝票明細(ISEG)はMATDOCに組み込まれます。"
                           "棚卸プロセスはS/4HANAで再構成されています。",
            field_mapping={"IBLNR": "IBLNR", "GJAHR": "MJAHR", "ZEESSION": "ZEESSION",
                           "MATNR": "MATNR", "WERKS": "WERKS", "LGORT": "LGORT"},
            auto_fix=False,
            notes="Physical inventory has additional process changes beyond table structure.",
        ))

        self._rules.append(SimplificationRule(
            rule_id="TABLE_MM_004",
            category="TABLE",
            sap_module="MM",
            severity="REVIEW",
            old_pattern="RKPF",
            new_pattern="RKPF (structure changed)",
            description="Reservation header (RKPF) structure has changed in S/4HANA. "
                        "Some fields are deprecated or moved. Review field usage.",
            description_ja="予約ヘッダ(RKPF)の構造がS/4HANAで変更されています。"
                           "一部のフィールドは廃止または移動されています。フィールド使用を確認してください。",
            field_mapping={},
            auto_fix=False,
            notes="RKPF still exists but with structural changes. Field-level review needed.",
        ))

    # ----------------------------------------------------------------
    # SD Table Rules
    # ----------------------------------------------------------------

    def _init_sd_rules(self):
        """Initialize SD table migration rules (3 rules)."""

        self._rules.append(SimplificationRule(
            rule_id="TABLE_SD_001",
            category="TABLE",
            sap_module="SD",
            severity="MANUAL",
            old_pattern="NAST",
            new_pattern="BRF+ Output Management",
            description="Output management table NAST is replaced by BRF+ (Business Rule Framework) "
                        "based output management in S/4HANA. Complete redesign of output determination.",
            description_ja="出力管理テーブルNASTはS/4HANAでBRF+(ビジネスルールフレームワーク)ベースの"
                           "出力管理に置き換えられます。出力決定の完全な再設計が必要です。",
            field_mapping={},
            auto_fix=False,
            notes="Output management is completely redesigned. NAST-based customizing must be "
                  "recreated in BRF+. This is one of the most impactful changes for SD.",
        ))

        self._rules.append(SimplificationRule(
            rule_id="TABLE_SD_002",
            category="TABLE",
            sap_module="SD",
            severity="REVIEW",
            old_pattern="VBKD",
            new_pattern="VBKD (restructured)",
            description="Sales document business data (VBKD) has been restructured in S/4HANA. "
                        "Some fields have moved to other tables or are deprecated.",
            description_ja="販売伝票業務データ(VBKD)はS/4HANAで再構成されています。"
                           "一部のフィールドは他のテーブルに移動または廃止されています。",
            field_mapping={},
            auto_fix=False,
            notes="Review all VBKD field references for compatibility.",
        ))

        self._rules.append(SimplificationRule(
            rule_id="TABLE_SD_003",
            category="TABLE",
            sap_module="SD",
            severity="REVIEW",
            old_pattern="KONV",
            new_pattern="PRCD_ELEMENTS",
            description="Pricing conditions (KONV) are replaced by PRCD_ELEMENTS in S/4HANA. "
                        "Pricing data model has been modernized.",
            description_ja="価格条件(KONV)はS/4HANAでPRCD_ELEMENTSに置き換えられます。"
                           "価格データモデルが刷新されています。",
            field_mapping={"KNUMV": "KNUMV", "KPOSN": "KPOSN", "STUNR": "STUNR",
                           "ZAESSION": "ZAESSION", "KSCHL": "KSCHL", "KBETR": "KBETR",
                           "KWERT": "KWERT", "WAERS": "WAERS"},
            auto_fix=False,
            notes="PRCD_ELEMENTS is a transparent table replacing cluster table KONV.",
        ))

    # ----------------------------------------------------------------
    # BP (Business Partner) Table Rules
    # ----------------------------------------------------------------

    def _init_bp_rules(self):
        """Initialize BP table migration rules (6 rules)."""

        kna1_but000_mapping = {
            "KUNNR": "PARTNER",
            "NAME1": "NAME_ORG1",
            "NAME2": "NAME_ORG2",
            "LAND1": "(via ADRC)",
            "ORT01": "(via ADRC)",
            "STRAS": "(via ADRC)",
            "PSTLZ": "(via ADRC)",
            "TELF1": "(via ADR2)",
            "TELFX": "(via ADR3)",
        }

        self._rules.append(SimplificationRule(
            rule_id="TABLE_BP_001",
            category="TABLE",
            sap_module="BP",
            severity="REVIEW",
            old_pattern="KNA1",
            new_pattern="BUT000",
            description="Customer general data (KNA1) is replaced by Business Partner (BUT000). "
                        "S/4HANA uses the Business Partner model for all customer/vendor master data. "
                        "Address data moves to ADRC/ADR2/ADR3.",
            description_ja="得意先一般データ(KNA1)はビジネスパートナー(BUT000)に置き換えられます。"
                           "S/4HANAでは全ての得意先/仕入先マスタデータにBPモデルを使用します。"
                           "住所データはADRC/ADR2/ADR3に移動します。",
            field_mapping=kna1_but000_mapping,
            auto_fix=False,
            notes="Business Partner is the central master data model in S/4HANA. "
                  "Customer-specific data is in CVI (Customer Vendor Integration) tables.",
        ))

        self._rules.append(SimplificationRule(
            rule_id="TABLE_BP_002",
            category="TABLE",
            sap_module="BP",
            severity="REVIEW",
            old_pattern="KNB1",
            new_pattern="BUT000",
            description="Customer company code data (KNB1) is replaced by BP role-based data. "
                        "Company code level attributes are managed through BP roles.",
            description_ja="得意先会社コードデータ(KNB1)はBPロールベースのデータに置き換えられます。"
                           "会社コードレベルの属性はBPロールを通じて管理されます。",
            field_mapping={"KUNNR": "PARTNER", "BUKRS": "BUKRS",
                           "AKONT": "(via BP role)", "ZTERM": "(via BP role)"},
            auto_fix=False,
            notes="Company code data managed through BP roles and CVI synchronization.",
        ))

        self._rules.append(SimplificationRule(
            rule_id="TABLE_BP_003",
            category="TABLE",
            sap_module="BP",
            severity="REVIEW",
            old_pattern="KNVV",
            new_pattern="BUT000",
            description="Customer sales data (KNVV) is replaced by BP role-based sales data. "
                        "Sales area attributes are managed through BP roles.",
            description_ja="得意先販売データ(KNVV)はBPロールベースの販売データに置き換えられます。"
                           "販売エリア属性はBPロールを通じて管理されます。",
            field_mapping={"KUNNR": "PARTNER", "VKORG": "VKORG", "VTWEG": "VTWEG",
                           "SPART": "SPART"},
            auto_fix=False,
            notes="Sales area data in CVI tables synchronized with BP.",
        ))

        lfa1_but000_mapping = {
            "LIFNR": "PARTNER",
            "NAME1": "NAME_ORG1",
            "NAME2": "NAME_ORG2",
            "LAND1": "(via ADRC)",
            "ORT01": "(via ADRC)",
            "STRAS": "(via ADRC)",
            "PSTLZ": "(via ADRC)",
        }

        self._rules.append(SimplificationRule(
            rule_id="TABLE_BP_004",
            category="TABLE",
            sap_module="BP",
            severity="REVIEW",
            old_pattern="LFA1",
            new_pattern="BUT000",
            description="Vendor general data (LFA1) is replaced by Business Partner (BUT000). "
                        "Vendor master is unified with customer master under BP model.",
            description_ja="仕入先一般データ(LFA1)はビジネスパートナー(BUT000)に置き換えられます。"
                           "仕入先マスタはBPモデルの下で得意先マスタと統合されます。",
            field_mapping=lfa1_but000_mapping,
            auto_fix=False,
            notes="Vendor data unified with customer data in BP model via CVI.",
        ))

        self._rules.append(SimplificationRule(
            rule_id="TABLE_BP_005",
            category="TABLE",
            sap_module="BP",
            severity="REVIEW",
            old_pattern="LFB1",
            new_pattern="BUT000",
            description="Vendor company code data (LFB1) is replaced by BP role-based data. "
                        "Company code level vendor attributes managed through BP roles.",
            description_ja="仕入先会社コードデータ(LFB1)はBPロールベースのデータに置き換えられます。"
                           "会社コードレベルの仕入先属性はBPロールを通じて管理されます。",
            field_mapping={"LIFNR": "PARTNER", "BUKRS": "BUKRS",
                           "AKONT": "(via BP role)", "ZTERM": "(via BP role)"},
            auto_fix=False,
            notes="Vendor company code data managed through BP roles.",
        ))

        self._rules.append(SimplificationRule(
            rule_id="TABLE_BP_006",
            category="TABLE",
            sap_module="BP",
            severity="REVIEW",
            old_pattern="LFM1",
            new_pattern="BUT000",
            description="Vendor purchasing data (LFM1) is replaced by BP role-based purchasing data. "
                        "Purchasing organization attributes managed through BP roles.",
            description_ja="仕入先購買データ(LFM1)はBPロールベースの購買データに置き換えられます。"
                           "購買組織属性はBPロールを通じて管理されます。",
            field_mapping={"LIFNR": "PARTNER", "EKORG": "EKORG",
                           "WAERS": "(via BP role)", "ZTERM": "(via BP role)"},
            auto_fix=False,
            notes="Purchasing organization data in CVI tables synchronized with BP.",
        ))

    # ----------------------------------------------------------------
    # ABAP Syntax Rules
    # ----------------------------------------------------------------

    def _init_abap_syntax_rules(self):
        """Initialize ABAP syntax modernization rules (10 rules)."""

        self._rules.append(SimplificationRule(
            rule_id="SYNTAX_001",
            category="SYNTAX",
            sap_module="ABAP",
            severity="AUTO",
            old_pattern=r"MOVE\s+(\S+)\s+TO\s+(\S+)",
            new_pattern=r"\2 = \1",
            description="Replace obsolete MOVE statement with inline assignment. "
                        "MOVE x TO y becomes y = x.",
            description_ja="廃止されたMOVE文をインライン代入に置き換えます。"
                           "MOVE x TO y は y = x になります。",
            auto_fix=True,
            notes="Simple regex replacement. Safe for automatic conversion.",
        ))

        self._rules.append(SimplificationRule(
            rule_id="SYNTAX_002",
            category="SYNTAX",
            sap_module="ABAP",
            severity="AUTO",
            old_pattern=r"COMPUTE\s+(\S+)\s*=\s*(.+)",
            new_pattern=r"\1 = \2",
            description="Remove obsolete COMPUTE keyword. COMPUTE y = expr becomes y = expr.",
            description_ja="廃止されたCOMPUTEキーワードを削除します。"
                           "COMPUTE y = expr は y = expr になります。",
            auto_fix=True,
            notes="Simple keyword removal. Safe for automatic conversion.",
        ))

        self._rules.append(SimplificationRule(
            rule_id="SYNTAX_003",
            category="SYNTAX",
            sap_module="ABAP",
            severity="AUTO",
            old_pattern=r"ADD\s+(\S+)\s+TO\s+(\S+)",
            new_pattern=r"\2 = \2 + \1",
            description="Replace obsolete ADD statement with arithmetic expression. "
                        "ADD x TO y becomes y = y + x.",
            description_ja="廃止されたADD文を算術式に置き換えます。"
                           "ADD x TO y は y = y + x になります。",
            auto_fix=True,
            notes="Simple regex replacement. Safe for automatic conversion.",
        ))

        self._rules.append(SimplificationRule(
            rule_id="SYNTAX_004",
            category="SYNTAX",
            sap_module="ABAP",
            severity="AUTO",
            old_pattern=r"SUBTRACT\s+(\S+)\s+FROM\s+(\S+)",
            new_pattern=r"\2 = \2 - \1",
            description="Replace obsolete SUBTRACT statement with arithmetic expression. "
                        "SUBTRACT x FROM y becomes y = y - x.",
            description_ja="廃止されたSUBTRACT文を算術式に置き換えます。"
                           "SUBTRACT x FROM y は y = y - x になります。",
            auto_fix=True,
            notes="Simple regex replacement. Safe for automatic conversion.",
        ))

        self._rules.append(SimplificationRule(
            rule_id="SYNTAX_005",
            category="SYNTAX",
            sap_module="ABAP",
            severity="AUTO",
            old_pattern=r"MULTIPLY\s+(\S+)\s+BY\s+(\S+)",
            new_pattern=r"\1 = \1 * \2",
            description="Replace obsolete MULTIPLY statement with arithmetic expression. "
                        "MULTIPLY y BY x becomes y = y * x.",
            description_ja="廃止されたMULTIPLY文を算術式に置き換えます。"
                           "MULTIPLY y BY x は y = y * x になります。",
            auto_fix=True,
            notes="Simple regex replacement. Safe for automatic conversion.",
        ))

        self._rules.append(SimplificationRule(
            rule_id="SYNTAX_006",
            category="SYNTAX",
            sap_module="ABAP",
            severity="AUTO",
            old_pattern=r"DIVIDE\s+(\S+)\s+BY\s+(\S+)",
            new_pattern=r"\1 = \1 / \2",
            description="Replace obsolete DIVIDE statement with arithmetic expression. "
                        "DIVIDE y BY x becomes y = y / x.",
            description_ja="廃止されたDIVIDE文を算術式に置き換えます。"
                           "DIVIDE y BY x は y = y / x になります。",
            auto_fix=True,
            notes="Simple regex replacement. Check for division by zero handling.",
        ))

        self._rules.append(SimplificationRule(
            rule_id="SYNTAX_007",
            category="SYNTAX",
            sap_module="ABAP",
            severity="REVIEW",
            old_pattern=r"TABLES\s+(\S+)",
            new_pattern=r"DATA \1 TYPE STANDARD TABLE OF \1 WITH DEFAULT KEY",
            description="Replace obsolete TABLES declaration with explicit DATA TYPE. "
                        "TABLES creates implicit work area which should be made explicit.",
            description_ja="廃止されたTABLES宣言を明示的なDATA TYPEに置き換えます。"
                           "TABLESは暗黙的なワークエリアを作成するため、明示的にする必要があります。",
            auto_fix=False,
            notes="TABLES creates header line and work area. Replacement needs context analysis "
                  "to determine correct type and work area usage.",
        ))

        self._rules.append(SimplificationRule(
            rule_id="SYNTAX_008",
            category="SYNTAX",
            sap_module="ABAP",
            severity="AUTO",
            old_pattern=r"RANGES\s+(\S+)\s+FOR\s+(\S+)",
            new_pattern=r"DATA \1 TYPE RANGE OF \2",
            description="Replace obsolete RANGES declaration with TYPE RANGE OF. "
                        "RANGES r FOR field becomes DATA r TYPE RANGE OF field.",
            description_ja="廃止されたRANGES宣言をTYPE RANGE OFに置き換えます。"
                           "RANGES r FOR field は DATA r TYPE RANGE OF field になります。",
            auto_fix=True,
            notes="Direct replacement. Field type reference is preserved.",
        ))

        self._rules.append(SimplificationRule(
            rule_id="SYNTAX_009",
            category="SYNTAX",
            sap_module="ABAP",
            severity="REVIEW",
            old_pattern=r"OCCURS\s+\d+",
            new_pattern="TYPE STANDARD TABLE OF",
            description="Replace obsolete OCCURS clause with typed internal table declaration. "
                        "OCCURS creates old-style internal tables with header lines.",
            description_ja="廃止されたOCCURS句を型付き内部テーブル宣言に置き換えます。"
                           "OCCURSはヘッダ行付きの旧式内部テーブルを作成します。",
            auto_fix=False,
            notes="Requires understanding the line type. Often combined with HEADER LINE removal.",
        ))

        self._rules.append(SimplificationRule(
            rule_id="SYNTAX_010",
            category="SYNTAX",
            sap_module="ABAP",
            severity="REVIEW",
            old_pattern=r"WITH\s+HEADER\s+LINE",
            new_pattern="(remove, use explicit work area)",
            description="Remove HEADER LINE addition and use explicit work area. "
                        "Header lines are obsolete and cause ambiguity in modern ABAP.",
            description_ja="HEADER LINE追加を削除し、明示的なワークエリアを使用します。"
                           "ヘッダ行は廃止されており、モダンABAPでは曖昧さを引き起こします。",
            auto_fix=False,
            notes="Removing header lines requires updating all references that implicitly use "
                  "the header line as a work area. Complex refactoring needed.",
        ))

    # ----------------------------------------------------------------
    # SQL Rules
    # ----------------------------------------------------------------

    def _init_sql_rules(self):
        """Initialize SQL migration rules (5 rules)."""

        self._rules.append(SimplificationRule(
            rule_id="SQL_001",
            category="SQL",
            sap_module="ABAP",
            severity="MANUAL",
            old_pattern=r"EXEC\s+SQL.*?ENDEXEC",
            new_pattern="Open SQL / ADBC (ABAP Database Connectivity)",
            description="Replace Native SQL (EXEC SQL...ENDEXEC) with Open SQL or ADBC. "
                        "Native SQL bypasses the database abstraction layer and is not portable.",
            description_ja="ネイティブSQL(EXEC SQL...ENDEXEC)をOpen SQLまたはADBCに置き換えます。"
                           "ネイティブSQLはデータベース抽象化レイヤーをバイパスし、移植性がありません。",
            auto_fix=False,
            notes="Native SQL is database-specific. Must be rewritten in Open SQL or use ADBC "
                  "for database-specific features. S/4HANA runs on HANA only.",
        ))

        self._rules.append(SimplificationRule(
            rule_id="SQL_002",
            category="SQL",
            sap_module="ABAP",
            severity="REVIEW",
            old_pattern=r"SELECT.*INTO\s+CORRESPONDING\s+FIELDS\s+OF",
            new_pattern="SELECT ... INTO @DATA(...) or explicit field list",
            description="Modernize SELECT INTO CORRESPONDING FIELDS to use inline declarations "
                        "or explicit field lists for better performance and clarity.",
            description_ja="SELECT INTO CORRESPONDING FIELDSをインライン宣言または明示的な"
                           "フィールドリストに刷新し、パフォーマンスと明確性を向上させます。",
            auto_fix=False,
            notes="INTO CORRESPONDING still works but inline DATA() is preferred in S/4HANA. "
                  "Review for performance optimization opportunities.",
        ))

        self._rules.append(SimplificationRule(
            rule_id="SQL_003",
            category="SQL",
            sap_module="ABAP",
            severity="AUTO",
            old_pattern=r"SELECT\s+.*\s+INTO\s+(?!@)",
            new_pattern="SELECT ... INTO @var / @DATA(...)",
            description="Add @ prefix to host variables in Open SQL statements. "
                        "Required for strict mode and new SQL syntax in S/4HANA.",
            description_ja="Open SQL文のホスト変数に@プレフィックスを追加します。"
                           "S/4HANAの厳格モードおよび新SQL構文で必須です。",
            auto_fix=True,
            notes="The @ escape for host variables is mandatory in strict mode. "
                  "Automated addition is generally safe.",
        ))

        self._rules.append(SimplificationRule(
            rule_id="SQL_004",
            category="SQL",
            sap_module="ABAP",
            severity="REVIEW",
            old_pattern=r"SELECT\s+.*\s+FROM\s+(BSEG|KONV|BSET|RFBLG|ATAB)",
            new_pattern="CDS View or replacement transparent table (e.g., ACDOCA, PRCD_ELEMENTS)",
            description="Replace SELECT on cluster tables (BSEG, KONV, etc.) with CDS views "
                        "or replacement transparent tables. Cluster tables are decomposed in S/4HANA.",
            description_ja="クラスタテーブル(BSEG, KONV等)へのSELECTをCDSビューまたは"
                           "置換透過テーブルに置き換えます。クラスタテーブルはS/4HANAで分解されます。",
            auto_fix=False,
            notes="Cluster tables become compatibility views. Performance may degrade. "
                  "Use ACDOCA for BSEG, PRCD_ELEMENTS for KONV.",
        ))

        self._rules.append(SimplificationRule(
            rule_id="SQL_005",
            category="SQL",
            sap_module="ABAP",
            severity="REVIEW",
            old_pattern=r"SELECT\s+.*\.\s*\n.*ENDSELECT",
            new_pattern="SELECT ... INTO TABLE @DATA(lt_result)",
            description="Replace SELECT...ENDSELECT loop with bulk SELECT INTO TABLE. "
                        "Row-by-row processing is inefficient, especially on HANA.",
            description_ja="SELECT...ENDSELECTループをバルクSELECT INTO TABLEに置き換えます。"
                           "行単位の処理は特にHANAでは非効率的です。",
            auto_fix=False,
            notes="SELECT...ENDSELECT performs row-by-row data transfer. Bulk fetch with "
                  "INTO TABLE is strongly recommended for HANA performance.",
        ))

    # ----------------------------------------------------------------
    # Function Module Rules
    # ----------------------------------------------------------------

    def _init_fm_rules(self):
        """Initialize function module migration rules (8 FM + 8 BAPI = 16 rules)."""

        # Function Modules
        self._rules.append(SimplificationRule(
            rule_id="FM_001",
            category="FUNCTION_MODULE",
            sap_module="CROSS",
            severity="REVIEW",
            old_pattern="REUSE_ALV_GRID_DISPLAY",
            new_pattern="cl_salv_table=>factory( )",
            description="Replace REUSE_ALV_GRID_DISPLAY with SALV (Simple ALV) model. "
                        "cl_salv_table provides a modern, object-oriented ALV framework.",
            description_ja="REUSE_ALV_GRID_DISPLAYをSALV(Simple ALV)モデルに置き換えます。"
                           "cl_salv_tableはモダンなオブジェクト指向ALVフレームワークを提供します。",
            auto_fix=False,
            notes="REUSE_ALV still works but SALV is the strategic direction. "
                  "Parameter mapping requires significant refactoring.",
        ))

        self._rules.append(SimplificationRule(
            rule_id="FM_002",
            category="FUNCTION_MODULE",
            sap_module="CROSS",
            severity="REVIEW",
            old_pattern="REUSE_ALV_LIST_DISPLAY",
            new_pattern="cl_salv_table=>factory( )",
            description="Replace REUSE_ALV_LIST_DISPLAY with SALV model. "
                        "List-based ALV should migrate to cl_salv_table.",
            description_ja="REUSE_ALV_LIST_DISPLAYをSALVモデルに置き換えます。"
                           "リストベースのALVはcl_salv_tableに移行すべきです。",
            auto_fix=False,
            notes="List ALV is even more outdated than grid ALV. Migration to SALV recommended.",
        ))

        self._rules.append(SimplificationRule(
            rule_id="FM_003",
            category="FUNCTION_MODULE",
            sap_module="CROSS",
            severity="AUTO",
            old_pattern="CONVERSION_EXIT_ALPHA_INPUT",
            new_pattern="|{ var ALPHA = IN }|",
            description="Replace CONVERSION_EXIT_ALPHA_INPUT with string template. "
                        "String templates with ALPHA = IN provide the same functionality inline.",
            description_ja="CONVERSION_EXIT_ALPHA_INPUTを文字列テンプレートに置き換えます。"
                           "ALPHA = IN付きの文字列テンプレートは同じ機能をインラインで提供します。",
            auto_fix=True,
            notes="String template replacement is clean and performant.",
        ))

        self._rules.append(SimplificationRule(
            rule_id="FM_004",
            category="FUNCTION_MODULE",
            sap_module="CROSS",
            severity="AUTO",
            old_pattern="CONVERSION_EXIT_ALPHA_OUTPUT",
            new_pattern="|{ var ALPHA = OUT }|",
            description="Replace CONVERSION_EXIT_ALPHA_OUTPUT with string template. "
                        "String templates with ALPHA = OUT provide the same functionality inline.",
            description_ja="CONVERSION_EXIT_ALPHA_OUTPUTを文字列テンプレートに置き換えます。"
                           "ALPHA = OUT付きの文字列テンプレートは同じ機能をインラインで提供します。",
            auto_fix=True,
            notes="String template replacement is clean and performant.",
        ))

        self._rules.append(SimplificationRule(
            rule_id="FM_005",
            category="FUNCTION_MODULE",
            sap_module="CROSS",
            severity="REVIEW",
            old_pattern="POPUP_TO_CONFIRM",
            new_pattern="cl_ci_query_attributes=>generic( )",
            description="Replace POPUP_TO_CONFIRM with modern dialog class. "
                        "Consider Fiori-compatible dialog patterns for S/4HANA.",
            description_ja="POPUP_TO_CONFIRMをモダンなダイアログクラスに置き換えます。"
                           "S/4HANAではFiori互換のダイアログパターンを検討してください。",
            auto_fix=False,
            notes="Popup FMs still work in GUI but not in Fiori. Consider UI5 alternatives.",
        ))

        self._rules.append(SimplificationRule(
            rule_id="FM_006",
            category="FUNCTION_MODULE",
            sap_module="MM",
            severity="MANUAL",
            old_pattern="MB_CREATE_GOODS_MOVEMENT",
            new_pattern="New Goods Movement API / InboundDelivery API",
            description="Replace MB_CREATE_GOODS_MOVEMENT with new S/4HANA API. "
                        "Material document creation uses new APIs in S/4HANA.",
            description_ja="MB_CREATE_GOODS_MOVEMENTを新しいS/4HANA APIに置き換えます。"
                           "入出庫伝票作成はS/4HANAの新しいAPIを使用します。",
            auto_fix=False,
            notes="The FM still works but the new API provides better integration with MATDOC.",
        ))

        self._rules.append(SimplificationRule(
            rule_id="FM_007",
            category="FUNCTION_MODULE",
            sap_module="SD",
            severity="MANUAL",
            old_pattern="NAST_OUTPUT_SEND",
            new_pattern="BRF+ Output Management Framework",
            description="Replace NAST_OUTPUT_SEND with BRF+ based output management. "
                        "Classic output determination via NAST is replaced in S/4HANA.",
            description_ja="NAST_OUTPUT_SENDをBRF+ベースの出力管理に置き換えます。"
                           "NASTによる従来の出力決定はS/4HANAで置き換えられます。",
            auto_fix=False,
            notes="Complete redesign of output processing. Requires BRF+ configuration.",
        ))

        self._rules.append(SimplificationRule(
            rule_id="FM_008",
            category="FUNCTION_MODULE",
            sap_module="CROSS",
            severity="REVIEW",
            old_pattern="GUI_DOWNLOAD",
            new_pattern="cl_gui_frontend_services=>gui_download( )",
            description="Replace GUI_DOWNLOAD function module with cl_gui_frontend_services method. "
                        "The class method is the modern replacement.",
            description_ja="GUI_DOWNLOAD汎用モジュールをcl_gui_frontend_servicesメソッドに置き換えます。"
                           "クラスメソッドがモダンな代替手段です。",
            auto_fix=False,
            notes="GUI_DOWNLOAD still works but the class is preferred. Note: neither works "
                  "in Fiori/Web scenarios.",
        ))

        # BAPIs
        self._rules.append(SimplificationRule(
            rule_id="BAPI_001",
            category="BAPI",
            sap_module="BP",
            severity="MANUAL",
            old_pattern="BAPI_CUSTOMER_CREATEFROMDATA1",
            new_pattern="CL_MD_BP_MAINTAIN=>maintain( )",
            description="Replace customer creation BAPI with Business Partner API. "
                        "Customer creation must go through BP in S/4HANA.",
            description_ja="得意先作成BAPIをビジネスパートナーAPIに置き換えます。"
                           "S/4HANAでは得意先作成はBPを経由する必要があります。",
            auto_fix=False,
            notes="Complete API change. Parameter structures are entirely different. "
                  "CVI synchronization creates the customer view automatically.",
        ))

        self._rules.append(SimplificationRule(
            rule_id="BAPI_002",
            category="BAPI",
            sap_module="BP",
            severity="MANUAL",
            old_pattern="BAPI_CUSTOMER_CHANGEFROMDATA1",
            new_pattern="CL_MD_BP_MAINTAIN=>maintain( )",
            description="Replace customer change BAPI with Business Partner API. "
                        "Customer modifications must go through BP in S/4HANA.",
            description_ja="得意先変更BAPIをビジネスパートナーAPIに置き換えます。"
                           "S/4HANAでは得意先変更はBPを経由する必要があります。",
            auto_fix=False,
            notes="Same API as creation. Use action parameter to differentiate.",
        ))

        self._rules.append(SimplificationRule(
            rule_id="BAPI_003",
            category="BAPI",
            sap_module="BP",
            severity="REVIEW",
            old_pattern="BAPI_CUSTOMER_GETDETAIL",
            new_pattern="CL_MD_BP_MAINTAIN=>get_detail( )",
            description="Replace customer detail BAPI with Business Partner read API. "
                        "Customer data retrieval should use BP APIs.",
            description_ja="得意先詳細BAPIをビジネスパートナー読取APIに置き換えます。"
                           "得意先データ取得はBP APIを使用すべきです。",
            auto_fix=False,
            notes="Read-only BAPI. BP get_detail returns unified partner data.",
        ))

        self._rules.append(SimplificationRule(
            rule_id="BAPI_004",
            category="BAPI",
            sap_module="BP",
            severity="MANUAL",
            old_pattern="BAPI_VENDOR_CREATE",
            new_pattern="CL_MD_BP_MAINTAIN=>maintain( )",
            description="Replace vendor creation BAPI with Business Partner API. "
                        "Vendor creation must go through BP in S/4HANA.",
            description_ja="仕入先作成BAPIをビジネスパートナーAPIに置き換えます。"
                           "S/4HANAでは仕入先作成はBPを経由する必要があります。",
            auto_fix=False,
            notes="Vendor creation through BP with vendor role assignment.",
        ))

        self._rules.append(SimplificationRule(
            rule_id="BAPI_005",
            category="BAPI",
            sap_module="BP",
            severity="MANUAL",
            old_pattern="BAPI_VENDOR_CHANGE",
            new_pattern="CL_MD_BP_MAINTAIN=>maintain( )",
            description="Replace vendor change BAPI with Business Partner API. "
                        "Vendor modifications must go through BP in S/4HANA.",
            description_ja="仕入先変更BAPIをビジネスパートナーAPIに置き換えます。"
                           "S/4HANAでは仕入先変更はBPを経由する必要があります。",
            auto_fix=False,
            notes="Same maintain API with vendor-specific parameters.",
        ))

        self._rules.append(SimplificationRule(
            rule_id="BAPI_006",
            category="BAPI",
            sap_module="BP",
            severity="REVIEW",
            old_pattern="BAPI_VENDOR_GETDETAIL",
            new_pattern="CL_MD_BP_MAINTAIN=>get_detail( )",
            description="Replace vendor detail BAPI with Business Partner read API. "
                        "Vendor data retrieval should use BP APIs.",
            description_ja="仕入先詳細BAPIをビジネスパートナー読取APIに置き換えます。"
                           "仕入先データ取得はBP APIを使用すべきです。",
            auto_fix=False,
            notes="Read-only BAPI. BP get_detail returns unified partner data.",
        ))

        self._rules.append(SimplificationRule(
            rule_id="BAPI_007",
            category="BAPI",
            sap_module="FI",
            severity="REVIEW",
            old_pattern="BAPI_ACC_DOCUMENT_POST",
            new_pattern="BAPI_ACC_DOCUMENT_POST (parameter changes in S/4HANA)",
            description="BAPI_ACC_DOCUMENT_POST remains but some parameters have changed. "
                        "Review extension structures and new mandatory fields for S/4HANA.",
            description_ja="BAPI_ACC_DOCUMENT_POSTは残りますが、一部のパラメータが変更されています。"
                           "S/4HANAの拡張構造と新しい必須フィールドを確認してください。",
            auto_fix=False,
            notes="BAPI still exists but EXTENSION2 structure changes. "
                  "New fields for Universal Journal may be required.",
        ))

        self._rules.append(SimplificationRule(
            rule_id="BAPI_008",
            category="BAPI",
            sap_module="MM",
            severity="REVIEW",
            old_pattern="BAPI_GOODSMVT_CREATE",
            new_pattern="BAPI_GOODSMVT_CREATE (new material document API)",
            description="BAPI_GOODSMVT_CREATE remains but creates MATDOC entries instead of MKPF/MSEG. "
                        "Review parameter usage for compatibility with new data model.",
            description_ja="BAPI_GOODSMVT_CREATEは残りますが、MKPF/MSEGの代わりにMATDOCエントリを"
                           "作成します。新しいデータモデルとの互換性のためパラメータ使用を確認してください。",
            auto_fix=False,
            notes="BAPI works but underlying storage changed to MATDOC. "
                  "Return values may differ.",
        ))

    # ----------------------------------------------------------------
    # Cross-Module Rules
    # ----------------------------------------------------------------

    def _init_cross_module_rules(self):
        """Initialize cross-module rules (4 rules)."""

        self._rules.append(SimplificationRule(
            rule_id="CROSS_001",
            category="TRANSACTION",
            sap_module="CROSS",
            severity="REVIEW",
            old_pattern="NUMBER_GET_NEXT",
            new_pattern="cl_uuid_factory=>create_system_uuid( )->create_uuid_x16( )",
            description="Consider replacing sequential number ranges with UUID-based identifiers. "
                        "UUIDs provide better performance in distributed/HANA environments.",
            description_ja="連番番号範囲をUUIDベースの識別子への置き換えを検討してください。"
                           "UUIDは分散/HANA環境でより良いパフォーマンスを提供します。",
            auto_fix=False,
            notes="Not all number ranges can be replaced with UUIDs. Evaluate case by case. "
                  "External number ranges with business meaning should be kept.",
        ))

        self._rules.append(SimplificationRule(
            rule_id="CROSS_002",
            category="TRANSACTION",
            sap_module="CROSS",
            severity="REVIEW",
            old_pattern="BDC_INSERT",
            new_pattern="(review BDC recordings for S/4HANA transaction compatibility)",
            description="Review BDC (Batch Data Communication) recordings for S/4HANA compatibility. "
                        "Many transactions have changed screens or been replaced in S/4HANA.",
            description_ja="BDC(バッチデータ通信)記録のS/4HANA互換性を確認してください。"
                           "多くのトランザクションはS/4HANAで画面変更または置換されています。",
            auto_fix=False,
            notes="BDC recordings are fragile and break with screen changes. "
                  "Consider API-based alternatives.",
        ))

        self._rules.append(SimplificationRule(
            rule_id="CROSS_003",
            category="TRANSACTION",
            sap_module="CROSS",
            severity="MANUAL",
            old_pattern="WRITE:",
            new_pattern="CDS View + Fiori Elements / cl_salv_table",
            description="Classic WRITE-based reports should be replaced with CDS views and Fiori apps. "
                        "WRITE statements produce list output incompatible with Fiori.",
            description_ja="従来のWRITEベースのレポートはCDSビューとFioriアプリに置き換えるべきです。"
                           "WRITE文はFioriと互換性のないリスト出力を生成します。",
            auto_fix=False,
            notes="Major effort. WRITE reports work in SAP GUI but not Fiori. "
                  "Full UI redesign needed for Fiori migration.",
        ))

        self._rules.append(SimplificationRule(
            rule_id="CROSS_004",
            category="TRANSACTION",
            sap_module="CROSS",
            severity="REVIEW",
            old_pattern="CALL TRANSACTION",
            new_pattern="(check for deprecated or changed transactions in S/4HANA)",
            description="Review CALL TRANSACTION statements for deprecated or changed transactions. "
                        "Many transaction codes have been removed or replaced in S/4HANA.",
            description_ja="廃止または変更されたトランザクションのCALL TRANSACTION文を確認してください。"
                           "多くのトランザクションコードはS/4HANAで削除または置換されています。",
            auto_fix=False,
            notes="Check against SAP's deprecated transaction code list. "
                  "Some tcodes redirect automatically, others are removed.",
        ))
