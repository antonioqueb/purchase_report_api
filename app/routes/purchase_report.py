from flask import Blueprint, request, jsonify
from app.services.odoo_service import get_partial_and_unreceived_purchase_lines

purchase_report_bp = Blueprint('purchase_report', __name__)

@purchase_report_bp.route('/api/purchase-report', methods=['GET'])
def purchase_report():
    start_date = request.args.get('start')
    end_date = request.args.get('end')

    if not start_date or not end_date:
        return jsonify({"error": "Parámetros 'start' y 'end' son requeridos en formato YYYY-MM-DD"}), 400

    try:
        data = get_partial_and_unreceived_purchase_lines(start_date, end_date)
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
