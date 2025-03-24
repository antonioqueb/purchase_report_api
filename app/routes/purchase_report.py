from flask import Blueprint, request, jsonify, render_template, send_file, redirect, url_for
from app.services.odoo_service import get_partial_and_unreceived_purchase_lines
import pandas as pd
from io import BytesIO
from datetime import datetime

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

    # Estilos ajustados coherentes con HTML
    title_format = workbook.add_format({
        'bold': True, 
        'bg_color': '#0f2385',  # Color primario
        'font_color': '#FFFFFF',
        'border': 1,
        'align': 'center',
        'valign': 'vcenter'
    })

    header_format = workbook.add_format({
        'bold': True, 
        'bg_color': '#4d9c28',  # Color secundario
        'font_color': '#FFFFFF',
        'border': 1,
        'align': 'center',
        'valign': 'vcenter'
    })

    cell_format = workbook.add_format({
        'border': 1,
        'valign': 'vcenter'
    })

    date_format = workbook.add_format({
        'border': 1,
        'valign': 'vcenter',
        'num_format': 'dd/mm/yyyy'
    })

    row = 0
    for producto in data:
        # Título del producto con colores corporativos
        worksheet.merge_range(row, 0, row, 7, f"{producto['producto']} (Unidad: {producto['unidad']})", title_format)
        row += 1

        # Encabezados
        headers = ['Orden de Compra', 'Proveedor', 'Fecha', 'Comprador', 'Planta',
                   'Cantidad Demandada', 'Cantidad Recepcionada', 'Cantidad Pendiente']
        for col, header in enumerate(headers):
            worksheet.write(row, col, header, header_format)
        row += 1

        # Datos de órdenes
        for orden in producto['ordenes']:
            worksheet.write(row, 0, orden['orden_compra'], cell_format)
            worksheet.write(row, 1, orden['proveedor'], cell_format)
            
            # Formato de fecha
            fecha_completa = datetime.strptime(orden['fecha_orden'], '%Y-%m-%d %H:%M:%S')
worksheet.write_datetime(row, 2, fecha_completa, date_format)
            
            worksheet.write(row, 3, orden['comprador'], cell_format)
            worksheet.write(row, 4, orden['planta'], cell_format)
            worksheet.write_number(row, 5, orden['cantidad_demandada'], cell_format)
            worksheet.write_number(row, 6, orden['cantidad_recepcionada'], cell_format)
            worksheet.write_number(row, 7, orden['cantidad_pendiente'], cell_format)
            row += 1

        # Espacio entre productos
        row += 1

    # Ajuste automático de columnas para mejorar presentación
    worksheet.set_column('A:A', 20)  # Orden de compra
    worksheet.set_column('B:B', 25)  # Proveedor
    worksheet.set_column('C:C', 15)  # Fecha
    worksheet.set_column('D:D', 20)  # Comprador
    worksheet.set_column('E:E', 15)  # Planta
    worksheet.set_column('F:H', 20)  # Cantidades numéricas

    workbook.close()
    output.seek(0)

    return send_file(output, download_name='reporte_compras.xlsx', as_attachment=True)
