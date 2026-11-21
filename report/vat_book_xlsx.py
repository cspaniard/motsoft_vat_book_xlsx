from collections import OrderedDict
from odoo import models


NUM_FORMAT = "#,##0.00 €"
DATE_FORMAT = "dd/mm/yy"
FONT_NAME = "Arial"
FONT_SIZE = 10


class MotsoftVatBookXlsx(models.AbstractModel):
    _name = "report.motsoft_vat_book_xlsx.vat_book_xlsx"
    _inherit = "report.report_xlsx.abstract"
    _description = "Libro de IVA XLSX"

    # ------------------------------------------------------------------
    # Entrada principal
    # ------------------------------------------------------------------
    def generate_xlsx_report(self, workbook, _, objs):
        self._set_workbook_default_format(workbook)
        formats = self._get_formats(workbook)

        for idx, book in enumerate(objs, 1):
            suffix = f' {book.year} - {book.period_type}'

            if book.period_type == '0A':
                suffix = f' {book.year} - Anual'

            self._write_sheet(
                workbook, formats, book,
                sheet_name="EMITIDAS" + suffix,
                title="LIBRO REGISTRO DE FACTURAS EMITIDAS",
                section_normal="Facturas emitidas",
                section_rect="Facturas rectificativas emitidas",
                lines=book.issued_line_ids,
                rect_lines=book.rectification_issued_line_ids,
            )
            self._write_sheet(
                workbook, formats, book,
                sheet_name="RECIBIDAS" + suffix,
                title="LIBRO REGISTRO DE FACTURAS RECIBIDAS",
                section_normal="Facturas recibidas",
                section_rect="Facturas rectificativas recibidas",
                lines=book.received_line_ids,
                rect_lines=book.rectification_received_line_ids,
            )

    # ------------------------------------------------------------------
    # Formato por defecto del libro (afecta también a celdas vacías)
    # ------------------------------------------------------------------
    def _set_workbook_default_format(self, workbook):
        default = workbook.formats[0]
        default.set_font_name(FONT_NAME)
        default.set_font_size(FONT_SIZE)
        default.set_align("vcenter")

    # ------------------------------------------------------------------
    # Formatos
    # ------------------------------------------------------------------
    def _get_formats(self, workbook):
        base = {
            "font_name": FONT_NAME,
            "font_size": FONT_SIZE,
            "valign": "vcenter",
        }

        def fmt(**kwargs):
            return workbook.add_format(dict(base, **kwargs))

        return {
            "title": fmt(bold=True, font_size=12),
            "bold": fmt(bold=True),
            "text": fmt(),
            "head_left": fmt(bold=True, align="left"),
            "head_right": fmt(bold=True, align="right"),
            "num": fmt(num_format=NUM_FORMAT, align="right"),
            "date": fmt(num_format=DATE_FORMAT, align="right"),
        }

    # ------------------------------------------------------------------
    # Hoja
    # ------------------------------------------------------------------
    def _write_sheet(self, workbook, formats, book, sheet_name, title,
                     section_normal, section_rect, lines, rect_lines):
        ws = workbook.add_worksheet(sheet_name)
        ws.set_column(0, 0, 22)  # Número
        ws.set_column(1, 1, 13)  # Fecha
        ws.set_column(2, 2, 42)  # Nombre
        ws.set_column(3, 3, 14)  # NIF
        ws.set_column(4, 4, 15)  # Base
        ws.set_column(5, 5, 42)  # Impuesto
        ws.set_column(6, 7, 15)  # Cuota, Total

        date_range = "%s-%s" % (
            book.date_start.strftime("%d/%m/%Y"),
            book.date_end.strftime("%d/%m/%Y"),
        )
        ws.write(0, 0, title, formats["title"])
        ws.write(2, 0, "Empresa:", formats["bold"])
        ws.write(2, 1, book.company_id.name or "", formats["text"])
        ws.write(3, 0, "Rango de fechas:", formats["bold"])
        ws.write(3, 1, date_range, formats["text"])
        ws.write(4, 0, "NIF:", formats["bold"])
        ws.write(4, 1, book.company_vat or "", formats["text"])

        row = 7
        row = self._write_invoice_section(ws, formats, row, section_normal, lines)
        row += 2
        row = self._write_invoice_section(ws, formats, row, section_rect, rect_lines)
        row += 2
        self._write_summary(ws, formats, row, lines | rect_lines)

    # ------------------------------------------------------------------
    # Sección de facturas
    # ------------------------------------------------------------------
    def _write_invoice_section(self, ws, f, row, section_title, lines):
        ws.write(row, 0, section_title, f["title"])
        row += 2
        headers = [
            ("Número", "head_left"),
            ("Fecha", "head_right"),
            ("Nombre Empresa", "head_left"),
            ("NIF", "head_left"),
            ("Base", "head_right"),
            ("Impuesto", "head_left"),
            ("Cuota", "head_right"),
            ("Total", "head_right"),
        ]
        for col, (text, fmt) in enumerate(headers):
            ws.write(row, col, text, f[fmt])
        row += 1

        for line in lines:
            rows = self._get_line_tax_rows(line)
            for i, (tax, base, quota) in enumerate(rows):
                if i == 0:
                    ws.write(row, 0, line.ref or line.move_id.name or "", f["text"])
                    if line.invoice_date:
                        ws.write_datetime(row, 1, line.invoice_date, f["date"])
                    ws.write(row, 2, line.partner_id.name or "", f["text"])
                    ws.write(row, 3, line.vat_number or "", f["text"])
                ws.write_number(row, 4, round(base, 2), f["num"])
                ws.write(row, 5, tax.name or "", f["text"])
                ws.write_number(row, 6, round(quota, 2), f["num"])
                ws.write_number(row, 7, round(base + quota, 2), f["num"])
                row += 1
        return row

    # ------------------------------------------------------------------
    # Resumen (valores calculados, sin fórmulas ni totales)
    # ------------------------------------------------------------------
    def _write_summary(self, ws, f, row, all_lines):
        ws.write(row, 0, "Resumen", f["title"])
        row += 2
        for col, (text, fmt) in {
            4: ("Base", "head_right"),
            5: ("Impuesto", "head_left"),
            6: ("Cuota", "head_right"),
            7: ("Total", "head_right"),
        }.items():
            ws.write(row, col, text, f[fmt])
        row += 1

        summary = OrderedDict()

        for line in all_lines:
            for tax, base, quota in self._get_line_tax_rows(line):
                if not tax:
                    # Filas sin impuesto: como antes, no entran en el resumen
                    continue
                vals = summary.setdefault(tax, [0.0, 0.0])
                vals[0] += base
                vals[1] += quota

        for tax in sorted(summary, key=lambda t: t.name or ""):
            base, quota = summary[tax]
            ws.write_number(row, 4, round(base, 2), f["num"])
            ws.write(row, 5, tax.name or "", f["text"])
            ws.write_number(row, 6, round(quota, 2), f["num"])
            ws.write_number(row, 7, round(base + quota, 2), f["num"])
            row += 1
        return row

    def _is_zero_base(self, amount):
        return self.env.company.currency_id.is_zero(amount)

    def _get_line_tax_rows(self, line):
        """Devuelve las filas (impuesto, base, cuota) que se imprimen en el
        detalle para una línea, ya sin las de base 0."""
        if line.tax_line_ids:
            rows = [
                (tl.tax_id, tl.base_amount, tl.tax_amount)
                for tl in line.tax_line_ids
            ]
        else:
            # Sin línea de impuesto: impuesto vacío
            rows = [(self.env["account.tax"], line.base_amount, line.tax_amount)]
        return [r for r in rows if not self._is_zero_base(r[1])]
