from flask import Blueprint, request, jsonify, render_template, send_file, redirect, url_for
from app.services.odoo_service import get_partial_and_unreceived_purchase_lines
import pandas as pd
from io import BytesIO

purchase_report_bp = Blueprint('purchase_report', __name__)

@purchase_report_bp.route('/', methods=['GET', 'POST'])
def index():
    data = []
    start = end = ""
    if request.method == 'POST':
        start = request.form['start_date']
        end = request.form['end_date']
        data = get_partial_and_unreceived_purchase_lines(start, end)
    return render_template('report.html', data=data, start=start, end=end)

@purchase_report_bp.route('/api/purchase-report', methods=['GET'])
def purchase_report_json():
    start_date = request.args.get('start')
    end_date = request.args.get('end')
    if not start_date or not end_date:
        return jsonify({"error": "Parámetros 'start' y 'end' son requeridos"}), 400
    data = get_partial_and_unreceived_purchase_lines(start_date, end_date)
    return jsonify(data)

@purchase_report_bp.route('/download', methods=['GET'])
def download_excel():
    start = request.args.get('start')
    end = request.args.get('end')
    data = get_partial_and_unreceived_purchase_lines(start, end)

    output = BytesIO()

    import xlsxwriter
    workbook = xlsxwriter.Workbook(output, {'in_memory': True})
    worksheet = workbook.add_worksheet('Reporte')

    # Estilos
    bold = workbook.add_format({'bold': True})
    header_format = workbook.add_format({'bold': True, 'bg_color': '#DDDDDD', 'border': 1})
    cell_format = workbook.add_format({'border': 1})
    title_format = workbook.add_format({'bold': True, 'bg_color': '#B7DEE8', 'border': 1})

    row = 0
    for producto in data:
        # Título del producto
        worksheet.merge_range(row, 0, row, 8, f"Producto: {producto['producto']} (Unidad: {producto['unidad']})", title_format)
        row += 1

        # Encabezado
        headers = ['Orden de Compra', 'Proveedor', 'Fecha', 'Comprador', 'Planta', 'Cantidad Demandada', 'Cantidad Recepcionada', 'Cantidad Pendiente']
        for col, header in enumerate(headers):
            worksheet.write(row, col, header, header_format)
        row += 1

        # Filas por orden
        for orden in producto['ordenes']:
            worksheet.write(row, 0, orden['orden_compra'], cell_format)
            worksheet.write(row, 1, orden['proveedor'], cell_format)
            worksheet.write(row, 2, orden['fecha_orden'], cell_format)
            worksheet.write(row, 3, orden['comprador'], cell_format)
            worksheet.write(row, 4, orden['planta'], cell_format)
            worksheet.write_number(row, 5, orden['cantidad_demandada'], cell_format)
            worksheet.write_number(row, 6, orden['cantidad_recepcionada'], cell_format)
            worksheet.write_number(row, 7, orden['cantidad_pendiente'], cell_format)
            row += 1

        # Espacio entre productos
        row += 1

    workbook.close()
    output.seek(0)

    return send_file(output, download_name='reporte_compras.xlsx', as_attachment=True)
