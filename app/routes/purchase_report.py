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

    rows = []
    for producto in data:
        for orden in producto['ordenes']:
            rows.append({
                'Producto': producto['producto'],
                'Unidad': producto['unidad'],
                'Orden de Compra': orden['orden_compra'],
                'Proveedor': orden['proveedor'],
                'Fecha de Orden': orden['fecha_orden'],
                'Comprador': orden['comprador'],
                'Planta': orden['planta'],
                'Cantidad Demandada': orden['cantidad_demandada'],
                'Cantidad Recepcionada': orden['cantidad_recepcionada'],
                'Cantidad Pendiente': orden['cantidad_pendiente']
            })

    df = pd.DataFrame(rows)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Reporte')
    output.seek(0)

    return send_file(output, download_name='reporte_compras.xlsx', as_attachment=True)
