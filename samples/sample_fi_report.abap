*&---------------------------------------------------------------------*
*& Report Z_FI_VENDOR_BALANCE
*&---------------------------------------------------------------------*
*& Sample ECC program for testing S/4HANA migration
*&---------------------------------------------------------------------*
REPORT z_fi_vendor_balance.

TABLES: lfa1, bsik.

DATA: gv_bukrs TYPE bukrs,
      gv_lifnr TYPE lifnr,
      gt_items TYPE TABLE OF bsik,
      gs_item  TYPE bsik,
      gv_total TYPE bsik-dmbtr.

RANGES: r_bukrs FOR bsik-bukrs.

SELECT-OPTIONS: s_bukrs FOR gv_bukrs,
                s_lifnr FOR gv_lifnr.

START-OF-SELECTION.

  MOVE s_bukrs TO r_bukrs.

  SELECT * FROM bsik
    INTO CORRESPONDING FIELDS OF gs_item
    WHERE bukrs IN s_bukrs
      AND lifnr IN s_lifnr.

    ADD gs_item-dmbtr TO gv_total.

    PERFORM write_line USING gs_item.

  ENDSELECT.

  SELECT * FROM bseg
    INTO CORRESPONDING FIELDS OF gs_item
    WHERE bukrs = gv_bukrs.
    WRITE: / gs_item-buzei, gs_item-dmbtr.
  ENDSELECT.

  CALL FUNCTION 'BAPI_VENDOR_GETDETAIL'
    EXPORTING
      vendorno = gv_lifnr
    IMPORTING
      return   = ls_return.

  CALL FUNCTION 'CONVERSION_EXIT_ALPHA_INPUT'
    EXPORTING
      input  = gv_lifnr
    IMPORTING
      output = gv_lifnr.

  CALL FUNCTION 'REUSE_ALV_GRID_DISPLAY'
    EXPORTING
      i_structure_name = 'BSIK'
    TABLES
      t_outtab         = gt_items.

  EXEC SQL.
    SELECT vendor_id, balance
      FROM zvendor_balance
      INTO :gv_lifnr, :gv_total
  ENDEXEC.

  COMPUTE gv_total = gv_total * 100.
  SUBTRACT 10 FROM gv_total.
  MULTIPLY gv_total BY 2.
  DIVIDE gv_total BY 3.

  WRITE: / 'Total Balance:', gv_total.

FORM write_line USING p_item TYPE bsik.
  WRITE: / p_item-bukrs, p_item-lifnr, p_item-dmbtr.
ENDFORM.
