*----------------------------------------------------------------------*
* S/4HANA Migration: ECC 6.08 → S/4HANA 2023
* Generated: 2026-04-03 06:11:25
* Tool: SAP ECC to S/4HANA Migration Tool v1.0
* Auto-converted: 1 | Review needed: 6 | Manual: 1
*----------------------------------------------------------------------*
REPORT z_test_program
TABLES lfa1
DATA gv_bukrs TYPE bukrs
DATA gv_total TYPE p DECIMALS 2
RANGES r_bukrs FOR lfa1-bukrs
MOVE gv_bukrs TO gv_total
* [S4-AUTO] [SYNTAX] COMPUTE gv_total = gv_total * 100 → gv_total = gv_total * 100
gv_total = gv_total * 100
ADD 10 TO gv_total
SUBTRACT 5 FROM gv_total
* [S4-REVIEW] [TABLE] BSIK → ACDOCA (PLEASE REVIEW)
* [S4-REVIEW] [TABLE] BSIK fields → Field mapping: BUKRS→RBUKRS, LIFNR→LIFNR, BELNR→BELNR, GJAHR→GJAHR, DMBTR→HSL... (PLEASE REVIEW)
* [S4-REVIEW] [SELECT_REWRITE] SELECT FROM BSIK → ACDOCA WHERE KOART = 'K' (PLEASE REVIEW)
* [S4-REVIEW] [SQL] INTO CORRESPONDING FIELDS OF gs_item → INTO @DATA(gs_item) (PLEASE REVIEW)
* [S4-REVIEW] [SQL] SELECT...ENDSELECT loop → SELECT...INTO TABLE (batch read) (PLEASE REVIEW)
SELECT * FROM ACDOCA INTO @DATA(gs_item) WHERE bukrs = gv_bukrs
WRITE / gs_item-dmbtr
ENDSELECT
* [S4-REVIEW] [BAPI] BAPI_VENDOR_GETDETAIL → CL_MD_BP_MAINTAIN=>get_detail( ) (PLEASE REVIEW)
CALL FUNCTION 'BAPI_VENDOR_GETDETAIL' EXPORTING vendorno = gv_lifnr IMPORTING return   = ls_return
* [S4-MANUAL] [SQL] EXEC SQL...ENDEXEC → Convert to Open SQL / ABAP SQL (MANUAL CONVERSION REQUIRED)
EXEC SQL