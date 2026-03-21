*&---------------------------------------------------------------------*
*& Report Z_MM_PURCHASE_ORDER
*&---------------------------------------------------------------------*
REPORT z_mm_purchase_order.

TABLES: ekko, ekpo.

DATA: gt_ekko TYPE TABLE OF ekko,
      gs_ekko TYPE ekko,
      gt_ekpo TYPE TABLE OF ekpo,
      gs_ekpo TYPE ekpo,
      gv_ebeln TYPE ebeln.

RANGES: r_ebeln FOR ekko-ebeln.

SELECT-OPTIONS: s_ebeln FOR gv_ebeln.

START-OF-SELECTION.

  MOVE s_ebeln TO r_ebeln.

  SELECT * FROM ekko
    INTO CORRESPONDING FIELDS OF gs_ekko
    WHERE ebeln IN s_ebeln.
    APPEND gs_ekko TO gt_ekko.
  ENDSELECT.

  LOOP AT gt_ekko INTO gs_ekko.
    SELECT * FROM ekpo
      INTO CORRESPONDING FIELDS OF gs_ekpo
      WHERE ebeln = gs_ekko-ebeln.
      APPEND gs_ekpo TO gt_ekpo.
    ENDSELECT.
  ENDLOOP.

  CALL FUNCTION 'BAPI_PO_GETDETAIL'
    EXPORTING
      purchaseorder = gv_ebeln
    IMPORTING
      return        = ls_return.

  CALL FUNCTION 'ME_READ_HISTORY'
    EXPORTING
      ebeln = gv_ebeln
    TABLES
      t_history = gt_history.

  COMPUTE gv_total = gs_ekpo-netpr * gs_ekpo-menge.
  ADD gv_total TO gv_grand_total.

  WRITE: / 'Purchase Order:', gv_ebeln.
  WRITE: / 'Total Value:', gv_total.

FORM display_item USING p_ekpo TYPE ekpo.
  WRITE: / p_ekpo-ebeln, p_ekpo-ebelp, p_ekpo-matnr, p_ekpo-netpr.
ENDFORM.
