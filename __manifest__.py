# -*- coding: utf-8 -*-
{
    'name': "Exportador Libros IVA a XLSX",

    'summary': """
        Exporta el libro de IVA (emitidas y recibidas) a XLSX desde el menú Imprimir
        """,

    'description': """
Exportación del Libro de IVA a XLSX
===================================

Este módulo añade la exportación a Excel (.xlsx) del libro registro de IVA,
generado a partir del modelo de libro de IVA existente. No añade modelos ni
vistas propias: únicamente proporciona el informe XLSX.

Funcionalidades
---------------
* Genera un único libro de Excel con dos hojas por cada libro de IVA:

  - **EMITIDAS**: Libro registro de facturas emitidas.
  - **RECIBIDAS**: Libro registro de facturas recibidas.

* El nombre de cada hoja incluye el año y el trimestre del periodo
  (por ejemplo, "EMITIDAS 2026 - T4").
* Cada hoja incluye una cabecera con el título del libro, la empresa, el
  rango de fechas y el NIF de la empresa.
* Cada hoja se divide en dos secciones:

  - Facturas (emitidas o recibidas).
  - Facturas rectificativas (emitidas o recibidas).

* Detalle por factura: número (referencia o nombre del asiento), fecha,
  nombre de la empresa, NIF, base, impuesto, cuota y total.
* Si una factura tiene varios impuestos, se muestra una fila por cada
  impuesto, indicando los datos de la factura solo en la primera fila.
* Se omiten las filas con base imponible igual a cero.
* Las facturas sin línea de impuesto se muestran con el impuesto vacío.
* Resumen al final de cada hoja con la base, la cuota y el total agrupados
  por impuesto (incluye facturas y rectificativas).

Notas técnicas
--------------
* Todos los importes se exportan como valores calculados (sin fórmulas).
* Requiere el módulo ``report_xlsx`` (OCA) y el módulo del libro de IVA
  sobre el que se genera el informe.    
    """,

    'author': "David Sanroma",
    'website': "",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Invoicing Management',
    'version': '15.0.0.1',

    # any module necessary for this one to work correctly
    'depends': [
        'l10n_es_vat_book',
        'report_xlsx'
    ],

    # always loaded
    'data': [
        'report/vat_book_xlsx.xml',
    ],
}
