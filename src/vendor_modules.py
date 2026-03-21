"""
SAP Module-Specific Handlers for ECC to S/4HANA Migration
==========================================================
Provides module detection, field mapping knowledge, deprecated transaction
lookups, and CDS view replacement information.
"""

from enum import Enum
from typing import Dict, List, Optional, Set, Tuple


class SapModuleType(Enum):
    """SAP module classification."""
    FI = "FI"
    CO = "CO"
    MM = "MM"
    SD = "SD"
    BP = "BP"
    PP = "PP"
    ABAP = "ABAP"
    CROSS = "CROSS"


# ---------------------------------------------------------------------------
# Table name to module mapping
# ---------------------------------------------------------------------------

TABLE_MODULE_MAP: Dict[str, SapModuleType] = {
    # FI tables
    "BKPF": SapModuleType.FI,
    "BSEG": SapModuleType.FI,
    "BSIS": SapModuleType.FI,
    "BSAS": SapModuleType.FI,
    "BSID": SapModuleType.FI,
    "BSAD": SapModuleType.FI,
    "BSIK": SapModuleType.FI,
    "BSAK": SapModuleType.FI,
    "SKA1": SapModuleType.FI,
    "SKB1": SapModuleType.FI,
    "ACDOCA": SapModuleType.FI,
    "GLT0": SapModuleType.FI,
    "FAGLFLEXA": SapModuleType.FI,
    "FAGLFLEXT": SapModuleType.FI,
    "ANLA": SapModuleType.FI,
    "ANLC": SapModuleType.FI,
    "ANLP": SapModuleType.FI,
    "T001": SapModuleType.FI,
    "T003": SapModuleType.FI,
    "TBSL": SapModuleType.FI,
    # CO tables
    "COSS": SapModuleType.CO,
    "COSP": SapModuleType.CO,
    "COBK": SapModuleType.CO,
    "CSKS": SapModuleType.CO,
    "CSKST": SapModuleType.CO,
    "CEPC": SapModuleType.CO,
    "CEPCT": SapModuleType.CO,
    "TKA01": SapModuleType.CO,
    "CSKA": SapModuleType.CO,
    "CSKT": SapModuleType.CO,
    # MM tables
    "MKPF": SapModuleType.MM,
    "MSEG": SapModuleType.MM,
    "MATDOC": SapModuleType.MM,
    "MARA": SapModuleType.MM,
    "MARC": SapModuleType.MM,
    "MARD": SapModuleType.MM,
    "MAKT": SapModuleType.MM,
    "EKKO": SapModuleType.MM,
    "EKPO": SapModuleType.MM,
    "EBAN": SapModuleType.MM,
    "ISEG": SapModuleType.MM,
    "RKPF": SapModuleType.MM,
    "RESB": SapModuleType.MM,
    "MBEW": SapModuleType.MM,
    "T156": SapModuleType.MM,
    # SD tables
    "VBAK": SapModuleType.SD,
    "VBAP": SapModuleType.SD,
    "VBRK": SapModuleType.SD,
    "VBRP": SapModuleType.SD,
    "LIKP": SapModuleType.SD,
    "LIPS": SapModuleType.SD,
    "NAST": SapModuleType.SD,
    "KONV": SapModuleType.SD,
    "PRCD_ELEMENTS": SapModuleType.SD,
    "VBKD": SapModuleType.SD,
    "VBFA": SapModuleType.SD,
    "VBPA": SapModuleType.SD,
    "TVAK": SapModuleType.SD,
    # BP tables
    "KNA1": SapModuleType.BP,
    "KNB1": SapModuleType.BP,
    "KNVV": SapModuleType.BP,
    "LFA1": SapModuleType.BP,
    "LFB1": SapModuleType.BP,
    "LFM1": SapModuleType.BP,
    "BUT000": SapModuleType.BP,
    "BUT020": SapModuleType.BP,
    "BUT021_FS": SapModuleType.BP,
    "ADRC": SapModuleType.BP,
    "ADR2": SapModuleType.BP,
    "ADR3": SapModuleType.BP,
    # PP tables
    "AFKO": SapModuleType.PP,
    "AFPO": SapModuleType.PP,
    "AFVC": SapModuleType.PP,
    "PLKO": SapModuleType.PP,
    "PLPO": SapModuleType.PP,
    "MAPL": SapModuleType.PP,
    "STKO": SapModuleType.PP,
    "STPO": SapModuleType.PP,
}

# ---------------------------------------------------------------------------
# Function module name prefix to module mapping
# ---------------------------------------------------------------------------

FM_MODULE_PREFIXES: Dict[str, SapModuleType] = {
    "BAPI_ACC": SapModuleType.FI,
    "BAPI_CUSTOMER": SapModuleType.BP,
    "BAPI_VENDOR": SapModuleType.BP,
    "BAPI_GOODSMVT": SapModuleType.MM,
    "BAPI_MATERIAL": SapModuleType.MM,
    "BAPI_PO_": SapModuleType.MM,
    "BAPI_SALESORDER": SapModuleType.SD,
    "BAPI_BILLING": SapModuleType.SD,
    "MB_": SapModuleType.MM,
    "SD_": SapModuleType.SD,
    "REUSE_ALV": SapModuleType.CROSS,
    "CONVERSION_EXIT": SapModuleType.CROSS,
    "POPUP_TO": SapModuleType.CROSS,
    "GUI_": SapModuleType.CROSS,
    "NAST_": SapModuleType.SD,
    "CO_": SapModuleType.CO,
    "FI_": SapModuleType.FI,
    "BAPI_FIXEDASSET": SapModuleType.FI,
    "BAPI_PRODORD": SapModuleType.PP,
}


# ---------------------------------------------------------------------------
# Field Mappings: old_table -> new_table -> {old_field: new_field}
# ---------------------------------------------------------------------------

_FIELD_MAPPINGS: Dict[Tuple[str, str], Dict[str, str]] = {
    # BSEG -> ACDOCA
    ("BSEG", "ACDOCA"): {
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
        "AUFNR": "AUFNR",
        "ANLN1": "ANLN1",
        "ANLN2": "ANLN2",
        "MWSKZ": "MWSKZ",
        "ZUONR": "ZUONR",
        "SGTXT": "SGTXT",
        "PROJK": "PS_PSP_PNR",
        "VBELN": "KDAUF",
        "VBELP": "KDPOS",
    },
    # BKPF -> ACDOCA (header fields available at line level)
    ("BKPF", "ACDOCA"): {
        "BUKRS": "RBUKRS",
        "BELNR": "BELNR",
        "GJAHR": "GJAHR",
        "BLART": "BLART",
        "BUDAT": "BUDAT",
        "BLDAT": "BLDAT",
        "MONAT": "POPER",
        "USNAM": "USNAM",
        "TCODE": "TCODE",
        "XBLNR": "XBLNR",
        "WAERS": "RWCUR",
    },
    # BSIS/BSAS -> ACDOCA
    ("BSIS", "ACDOCA"): {
        "BUKRS": "RBUKRS",
        "HKONT": "RACCT",
        "BELNR": "BELNR",
        "GJAHR": "GJAHR",
        "BUZEI": "DOCLN",
        "DMBTR": "HSL",
        "WRBTR": "TSL",
        "SHKZG": "DRCRK",
        "ZUONR": "ZUONR",
        "BUDAT": "BUDAT",
    },
    ("BSAS", "ACDOCA"): {
        "BUKRS": "RBUKRS",
        "HKONT": "RACCT",
        "BELNR": "BELNR",
        "GJAHR": "GJAHR",
        "BUZEI": "DOCLN",
        "DMBTR": "HSL",
        "WRBTR": "TSL",
        "SHKZG": "DRCRK",
        "AUGDT": "AUGDT",
        "AUGBL": "AUGBL",
    },
    # BSID/BSAD -> ACDOCA (customer subledger)
    ("BSID", "ACDOCA"): {
        "BUKRS": "RBUKRS",
        "KUNNR": "KUNNR",
        "BELNR": "BELNR",
        "GJAHR": "GJAHR",
        "BUZEI": "DOCLN",
        "DMBTR": "HSL",
        "WRBTR": "TSL",
        "SHKZG": "DRCRK",
    },
    ("BSAD", "ACDOCA"): {
        "BUKRS": "RBUKRS",
        "KUNNR": "KUNNR",
        "BELNR": "BELNR",
        "GJAHR": "GJAHR",
        "BUZEI": "DOCLN",
        "DMBTR": "HSL",
        "WRBTR": "TSL",
        "AUGDT": "AUGDT",
    },
    # BSIK/BSAK -> ACDOCA (vendor subledger)
    ("BSIK", "ACDOCA"): {
        "BUKRS": "RBUKRS",
        "LIFNR": "LIFNR",
        "BELNR": "BELNR",
        "GJAHR": "GJAHR",
        "BUZEI": "DOCLN",
        "DMBTR": "HSL",
        "WRBTR": "TSL",
        "SHKZG": "DRCRK",
    },
    ("BSAK", "ACDOCA"): {
        "BUKRS": "RBUKRS",
        "LIFNR": "LIFNR",
        "BELNR": "BELNR",
        "GJAHR": "GJAHR",
        "BUZEI": "DOCLN",
        "DMBTR": "HSL",
        "WRBTR": "TSL",
        "AUGDT": "AUGDT",
    },
    # FAGLFLEXA -> ACDOCA
    ("FAGLFLEXA", "ACDOCA"): {
        "RBUKRS": "RBUKRS",
        "BELNR": "BELNR",
        "GJAHR": "GJAHR",
        "DOCLN": "DOCLN",
        "RACCT": "RACCT",
        "RCNTR": "RCNTR",
        "PRCTR": "PRCTR",
        "RFAREA": "RFAREA",
        "RBUSA": "RBUSA",
        "KOKRS": "KOKRS",
        "SEGMENT": "SEGMENT",
        "HSL": "HSL",
        "TSL": "TSL",
        "DRCRK": "DRCRK",
    },
    # MKPF -> MATDOC
    ("MKPF", "MATDOC"): {
        "MBLNR": "MBLNR",
        "MJAHR": "MJAHR",
        "BUDAT": "BUDAT_MKPF",
        "BLDAT": "BLDAT",
        "USNAM": "USNAM",
        "BWART": "BWART",
        "XBLNR": "XBLNR",
        "VGART": "VGART",
        "CPUDT": "CPUDT_MKPF",
        "CPUTM": "CPUTM_MKPF",
    },
    # MSEG -> MATDOC
    ("MSEG", "MATDOC"): {
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
        "KOSTL": "KOSTL",
        "AUFNR": "AUFNR",
        "SOBKZ": "SOBKZ",
        "SHKZG": "SHKZG",
        "LGTYP": "LGTYP",
        "LGPLA": "LGPLA",
    },
    # KNA1 -> BUT000 (customer general data)
    ("KNA1", "BUT000"): {
        "KUNNR": "PARTNER",
        "NAME1": "NAME_ORG1",
        "NAME2": "NAME_ORG2",
        "LAND1": "(via ADRC.COUNTRY)",
        "ORT01": "(via ADRC.CITY1)",
        "STRAS": "(via ADRC.STREET)",
        "PSTLZ": "(via ADRC.POST_CODE1)",
        "REGIO": "(via ADRC.REGION)",
        "TELF1": "(via ADR2.TEL_NUMBER)",
        "TELFX": "(via ADR3.FAX_NUMBER)",
        "SPRAS": "BU_LANGU",
        "KTOKD": "(via CVI link table)",
        "STCD1": "PARTNER_GUID (via DFKKBPTAXNUM)",
        "STCD2": "PARTNER_GUID (via DFKKBPTAXNUM)",
        "KONZS": "BU_GROUP",
    },
    # LFA1 -> BUT000 (vendor general data)
    ("LFA1", "BUT000"): {
        "LIFNR": "PARTNER",
        "NAME1": "NAME_ORG1",
        "NAME2": "NAME_ORG2",
        "LAND1": "(via ADRC.COUNTRY)",
        "ORT01": "(via ADRC.CITY1)",
        "STRAS": "(via ADRC.STREET)",
        "PSTLZ": "(via ADRC.POST_CODE1)",
        "REGIO": "(via ADRC.REGION)",
        "TELF1": "(via ADR2.TEL_NUMBER)",
        "TELFX": "(via ADR3.FAX_NUMBER)",
        "SPRAS": "BU_LANGU",
        "KTOKK": "(via CVI link table)",
        "STCD1": "PARTNER_GUID (via DFKKBPTAXNUM)",
        "STCD2": "PARTNER_GUID (via DFKKBPTAXNUM)",
    },
    # KONV -> PRCD_ELEMENTS
    ("KONV", "PRCD_ELEMENTS"): {
        "KNUMV": "KNUMV",
        "KPOSN": "KPOSN",
        "STUNR": "STUNR",
        "ZAESSION": "ZAESSION",
        "KSCHL": "KSCHL",
        "KBETR": "KBETR",
        "KWERT": "KWERT",
        "WAERS": "WAERS",
        "KMEIN": "KMEIN",
        "KPEIN": "KPEIN",
    },
    # COSS -> ACDOCA
    ("COSS", "ACDOCA"): {
        "OBJNR": "OBJNR",
        "GJAHR": "GJAHR",
        "KSTAR": "RACCT",
        "WRTTP": "WRTTP",
        "VERSN": "VERSN",
    },
    # COSP -> ACDOCA
    ("COSP", "ACDOCA"): {
        "OBJNR": "OBJNR",
        "GJAHR": "GJAHR",
        "KSTAR": "RACCT",
        "WRTTP": "WRTTP",
        "VERSN": "VERSN",
    },
}


# ---------------------------------------------------------------------------
# Deprecated Transaction Codes
# ---------------------------------------------------------------------------

_DEPRECATED_TRANSACTIONS: Dict[str, Dict[str, str]] = {
    # FI transactions
    "FB01": {"replacement": "FB01 (still available)", "note": "Works but consider Fiori apps",
             "note_ja": "動作しますがFioriアプリの検討を推奨"},
    "FB02": {"replacement": "FB02 (still available)", "note": "Works but consider Fiori apps",
             "note_ja": "動作しますがFioriアプリの検討を推奨"},
    "FB03": {"replacement": "FB03 (still available)", "note": "Works but consider Fiori apps",
             "note_ja": "動作しますがFioriアプリの検討を推奨"},
    "FS00": {"replacement": "FS00 (still available)", "note": "GL account master, still works",
             "note_ja": "GL勘定マスタ、引き続き動作"},
    "F-28": {"replacement": "F-28 / Fiori app F0717", "note": "Incoming payment",
             "note_ja": "入金処理"},
    "F-53": {"replacement": "F-53 / Fiori app F0718", "note": "Outgoing payment",
             "note_ja": "出金処理"},
    # Customer/Vendor (replaced by BP)
    "XD01": {"replacement": "BP (tcode BP)", "note": "Customer create - replaced by Business Partner",
             "note_ja": "得意先作成 - ビジネスパートナーに置換"},
    "XD02": {"replacement": "BP (tcode BP)", "note": "Customer change - replaced by Business Partner",
             "note_ja": "得意先変更 - ビジネスパートナーに置換"},
    "XD03": {"replacement": "BP (tcode BP)", "note": "Customer display - replaced by Business Partner",
             "note_ja": "得意先照会 - ビジネスパートナーに置換"},
    "XK01": {"replacement": "BP (tcode BP)", "note": "Vendor create - replaced by Business Partner",
             "note_ja": "仕入先作成 - ビジネスパートナーに置換"},
    "XK02": {"replacement": "BP (tcode BP)", "note": "Vendor change - replaced by Business Partner",
             "note_ja": "仕入先変更 - ビジネスパートナーに置換"},
    "XK03": {"replacement": "BP (tcode BP)", "note": "Vendor display - replaced by Business Partner",
             "note_ja": "仕入先照会 - ビジネスパートナーに置換"},
    "FD01": {"replacement": "BP (tcode BP)", "note": "Customer create (FI) - replaced by BP",
             "note_ja": "得意先作成(FI) - BPに置換"},
    "FD02": {"replacement": "BP (tcode BP)", "note": "Customer change (FI) - replaced by BP",
             "note_ja": "得意先変更(FI) - BPに置換"},
    "FK01": {"replacement": "BP (tcode BP)", "note": "Vendor create (FI) - replaced by BP",
             "note_ja": "仕入先作成(FI) - BPに置換"},
    "FK02": {"replacement": "BP (tcode BP)", "note": "Vendor change (FI) - replaced by BP",
             "note_ja": "仕入先変更(FI) - BPに置換"},
    "MK01": {"replacement": "BP (tcode BP)", "note": "Vendor create (MM) - replaced by BP",
             "note_ja": "仕入先作成(MM) - BPに置換"},
    "MK02": {"replacement": "BP (tcode BP)", "note": "Vendor change (MM) - replaced by BP",
             "note_ja": "仕入先変更(MM) - BPに置換"},
    "VD01": {"replacement": "BP (tcode BP)", "note": "Customer create (SD) - replaced by BP",
             "note_ja": "得意先作成(SD) - BPに置換"},
    "VD02": {"replacement": "BP (tcode BP)", "note": "Customer change (SD) - replaced by BP",
             "note_ja": "得意先変更(SD) - BPに置換"},
    # MM transactions
    "MB01": {"replacement": "MIGO", "note": "Goods receipt - use MIGO in S/4HANA",
             "note_ja": "入庫 - S/4HANAではMIGOを使用"},
    "MB02": {"replacement": "MIGO", "note": "Change material doc - use MIGO",
             "note_ja": "入出庫伝票変更 - MIGOを使用"},
    "MB03": {"replacement": "MIGO", "note": "Display material doc - use MIGO",
             "note_ja": "入出庫伝票照会 - MIGOを使用"},
    "MB11": {"replacement": "MIGO", "note": "Goods movement - use MIGO",
             "note_ja": "入出庫転記 - MIGOを使用"},
    "MB1A": {"replacement": "MIGO", "note": "Goods issue - use MIGO",
             "note_ja": "出庫 - MIGOを使用"},
    "MB1B": {"replacement": "MIGO", "note": "Transfer posting - use MIGO",
             "note_ja": "転送転記 - MIGOを使用"},
    "MB1C": {"replacement": "MIGO", "note": "Other goods receipt - use MIGO",
             "note_ja": "その他入庫 - MIGOを使用"},
    "MB31": {"replacement": "MIGO", "note": "GR for production order - use MIGO",
             "note_ja": "製造オーダー入庫 - MIGOを使用"},
    # SD transactions
    "VF01": {"replacement": "VF01 (still available)", "note": "Billing - works, consider Fiori",
             "note_ja": "請求書作成 - 動作、Fiori検討"},
    "VA01": {"replacement": "VA01 (still available)", "note": "Sales order - works, consider Fiori",
             "note_ja": "受注作成 - 動作、Fiori検討"},
    # Output
    "NACE": {"replacement": "BRF+ / Output Management", "note": "Output control - replaced by BRF+",
             "note_ja": "出力制御 - BRF+に置換"},
    # CO transactions
    "KS01": {"replacement": "KS01 (still available)", "note": "Cost center create - still works",
             "note_ja": "原価センタ作成 - 引き続き動作"},
    "KP06": {"replacement": "KP06 (still available)", "note": "Cost planning - still works",
             "note_ja": "原価計画 - 引き続き動作"},
}


# ---------------------------------------------------------------------------
# CDS View Replacements
# ---------------------------------------------------------------------------

_CDS_VIEW_REPLACEMENTS: Dict[str, Dict[str, str]] = {
    # FI CDS views
    "BSEG": {
        "cds_view": "I_JournalEntry",
        "description": "Universal Journal Entry line items",
        "description_ja": "ユニバーサルジャーナル仕訳明細",
    },
    "BKPF": {
        "cds_view": "I_JournalEntry",
        "description": "Journal entry (header fields included)",
        "description_ja": "仕訳(ヘッダフィールド含む)",
    },
    "BSIS": {
        "cds_view": "I_GLAccountLineItem",
        "description": "GL account line items (open)",
        "description_ja": "GL勘定明細(未消込)",
    },
    "BSAS": {
        "cds_view": "I_GLAccountLineItem",
        "description": "GL account line items (cleared)",
        "description_ja": "GL勘定明細(消込済)",
    },
    "BSID": {
        "cds_view": "I_CustomerLineItem",
        "description": "Customer line items (open)",
        "description_ja": "得意先明細(未消込)",
    },
    "BSAD": {
        "cds_view": "I_CustomerLineItem",
        "description": "Customer line items (cleared)",
        "description_ja": "得意先明細(消込済)",
    },
    "BSIK": {
        "cds_view": "I_SupplierLineItem",
        "description": "Supplier/vendor line items (open)",
        "description_ja": "仕入先明細(未消込)",
    },
    "BSAK": {
        "cds_view": "I_SupplierLineItem",
        "description": "Supplier/vendor line items (cleared)",
        "description_ja": "仕入先明細(消込済)",
    },
    "GLT0": {
        "cds_view": "I_GLAccountBalance",
        "description": "GL account balance (aggregated)",
        "description_ja": "GL勘定残高(集計)",
    },
    "FAGLFLEXA": {
        "cds_view": "I_JournalEntry",
        "description": "New GL line items via Universal Journal",
        "description_ja": "新GL明細(ユニバーサルジャーナル経由)",
    },
    "FAGLFLEXT": {
        "cds_view": "I_GLAccountBalance",
        "description": "New GL totals via balance CDS view",
        "description_ja": "新GL合計(残高CDSビュー経由)",
    },
    # CO CDS views
    "COSS": {
        "cds_view": "I_JournalEntryItem",
        "description": "CO internal postings via journal",
        "description_ja": "CO内部転記(ジャーナル経由)",
    },
    "COSP": {
        "cds_view": "I_JournalEntryItem",
        "description": "CO external postings via journal",
        "description_ja": "CO外部転記(ジャーナル経由)",
    },
    # MM CDS views
    "MKPF": {
        "cds_view": "I_MaterialDocumentHeader_2",
        "description": "Material document header",
        "description_ja": "入出庫伝票ヘッダ",
    },
    "MSEG": {
        "cds_view": "I_MaterialDocumentItem_2",
        "description": "Material document item",
        "description_ja": "入出庫伝票明細",
    },
    # SD CDS views
    "KONV": {
        "cds_view": "I_PricingElement",
        "description": "Pricing conditions / elements",
        "description_ja": "価格条件/エレメント",
    },
    "NAST": {
        "cds_view": "(BRF+ Output Management - no direct CDS replacement)",
        "description": "Output management replaced by BRF+",
        "description_ja": "出力管理はBRF+に置換",
    },
    # BP CDS views
    "KNA1": {
        "cds_view": "I_Customer",
        "description": "Customer master (CVI-compatible view)",
        "description_ja": "得意先マスタ(CVI互換ビュー)",
    },
    "LFA1": {
        "cds_view": "I_Supplier",
        "description": "Supplier/vendor master (CVI-compatible view)",
        "description_ja": "仕入先マスタ(CVI互換ビュー)",
    },
    "BUT000": {
        "cds_view": "I_BusinessPartner",
        "description": "Business Partner master",
        "description_ja": "ビジネスパートナーマスタ",
    },
    # Asset CDS views
    "ANLA": {
        "cds_view": "I_FixedAsset",
        "description": "Fixed asset master",
        "description_ja": "固定資産マスタ",
    },
    "ANLC": {
        "cds_view": "I_FixedAssetValue_2",
        "description": "Fixed asset values",
        "description_ja": "固定資産価額",
    },
}


# ---------------------------------------------------------------------------
# Public API Functions
# ---------------------------------------------------------------------------

def detect_sap_module(
    tables_used: Optional[List[str]] = None,
    fm_used: Optional[List[str]] = None,
) -> Set[SapModuleType]:
    """
    Auto-detect which SAP modules are involved based on tables and function modules used.

    Args:
        tables_used: List of table names referenced in the ABAP code.
        fm_used: List of function module / BAPI names referenced in the ABAP code.

    Returns:
        Set of SapModuleType enums representing the detected modules.
    """
    modules: Set[SapModuleType] = set()

    if tables_used:
        for table_name in tables_used:
            upper_name = table_name.upper().strip()
            if upper_name in TABLE_MODULE_MAP:
                modules.add(TABLE_MODULE_MAP[upper_name])

    if fm_used:
        for fm_name in fm_used:
            upper_name = fm_name.upper().strip()
            # Try exact match in prefix map (longest prefix first)
            matched = False
            for prefix in sorted(FM_MODULE_PREFIXES.keys(), key=len, reverse=True):
                if upper_name.startswith(prefix):
                    modules.add(FM_MODULE_PREFIXES[prefix])
                    matched = True
                    break
            # If no prefix match, default to CROSS for unknown FMs
            if not matched and upper_name.startswith("BAPI_"):
                modules.add(SapModuleType.CROSS)

    return modules


def get_field_mapping(old_table: str, new_table: str) -> Dict[str, str]:
    """
    Return field name mapping for a table migration.

    Args:
        old_table: The ECC table name (e.g., "BSEG").
        new_table: The S/4HANA replacement table name (e.g., "ACDOCA").

    Returns:
        Dictionary mapping old field names to new field names.
        Returns empty dict if no mapping is registered.
    """
    key = (old_table.upper().strip(), new_table.upper().strip())
    return dict(_FIELD_MAPPINGS.get(key, {}))


def get_all_field_mappings() -> Dict[Tuple[str, str], Dict[str, str]]:
    """Return a copy of all registered field mappings."""
    return {k: dict(v) for k, v in _FIELD_MAPPINGS.items()}


def get_deprecated_transactions() -> Dict[str, Dict[str, str]]:
    """
    Return dictionary of deprecated/changed transaction codes.

    Returns:
        Dict mapping old tcode to {"replacement": str, "note": str, "note_ja": str}.
    """
    return dict(_DEPRECATED_TRANSACTIONS)


def get_deprecated_transaction(tcode: str) -> Optional[Dict[str, str]]:
    """
    Look up a single transaction code for deprecation info.

    Args:
        tcode: The transaction code to check (e.g., "XD01").

    Returns:
        Dict with replacement info, or None if not deprecated/changed.
    """
    return _DEPRECATED_TRANSACTIONS.get(tcode.upper().strip())


def get_cds_view_replacements() -> Dict[str, Dict[str, str]]:
    """
    Return dictionary of table -> CDS view name replacements.

    Returns:
        Dict mapping table name to {"cds_view": str, "description": str, "description_ja": str}.
    """
    return dict(_CDS_VIEW_REPLACEMENTS)


def get_cds_view_for_table(table_name: str) -> Optional[Dict[str, str]]:
    """
    Look up the CDS view replacement for a specific table.

    Args:
        table_name: The table name to look up (e.g., "BSEG").

    Returns:
        Dict with CDS view info, or None if no replacement registered.
    """
    return _CDS_VIEW_REPLACEMENTS.get(table_name.upper().strip())


def get_module_for_table(table_name: str) -> Optional[SapModuleType]:
    """
    Return the SAP module for a given table name.

    Args:
        table_name: The table name to classify.

    Returns:
        SapModuleType or None if the table is not recognized.
    """
    return TABLE_MODULE_MAP.get(table_name.upper().strip())


def get_module_for_fm(fm_name: str) -> Optional[SapModuleType]:
    """
    Return the SAP module for a given function module name based on prefix matching.

    Args:
        fm_name: The function module name to classify.

    Returns:
        SapModuleType or None if no prefix match is found.
    """
    upper_name = fm_name.upper().strip()
    for prefix in sorted(FM_MODULE_PREFIXES.keys(), key=len, reverse=True):
        if upper_name.startswith(prefix):
            return FM_MODULE_PREFIXES[prefix]
    return None


def get_tables_for_module(module: SapModuleType) -> List[str]:
    """
    Return all known table names for a given SAP module.

    Args:
        module: The SapModuleType to filter by.

    Returns:
        Sorted list of table names belonging to the module.
    """
    return sorted(
        table for table, mod in TABLE_MODULE_MAP.items()
        if mod == module
    )


def get_replacement_table(old_table: str) -> Optional[str]:
    """
    Return the S/4HANA replacement table for an ECC table, if known.

    Args:
        old_table: The ECC table name.

    Returns:
        The replacement table name, or None.
    """
    _TABLE_REPLACEMENTS = {
        "BSEG": "ACDOCA",
        "BKPF": "ACDOCA",
        "BSIS": "ACDOCA",
        "BSAS": "ACDOCA",
        "BSID": "ACDOCA",
        "BSAD": "ACDOCA",
        "BSIK": "ACDOCA",
        "BSAK": "ACDOCA",
        "GLT0": "ACDOCA",
        "FAGLFLEXA": "ACDOCA",
        "FAGLFLEXT": "ACDOCA",
        "COSS": "ACDOCA",
        "COSP": "ACDOCA",
        "COBK": "ACDOCA",
        "ANLA": "ACDOCA",
        "ANLC": "ACDOCA",
        "MKPF": "MATDOC",
        "MSEG": "MATDOC",
        "ISEG": "MATDOC",
        "KNA1": "BUT000",
        "KNB1": "BUT000",
        "KNVV": "BUT000",
        "LFA1": "BUT000",
        "LFB1": "BUT000",
        "LFM1": "BUT000",
        "KONV": "PRCD_ELEMENTS",
    }
    return _TABLE_REPLACEMENTS.get(old_table.upper().strip())
