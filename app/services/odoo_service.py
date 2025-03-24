import os
import xmlrpc.client

url = os.getenv("ODOO_URL")
db = os.getenv("ODOO_DB")
user = os.getenv("ODOO_USER")
password = os.getenv("ODOO_PASSWORD")

common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
uid = common.authenticate(db, user, password, {})
models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object")

def get_partial_and_unreceived_purchase_lines(start_date: str, end_date: str):
    domain = [
        ('state', 'in', ['purchase', 'done']),
        ('order_id.date_order', '>=', start_date),
        ('order_id.date_order', '<=', end_date),
        ('qty_received', '<', 'product_qty')  # incluye qty_received = 0 y parcialmente recibidas
    ]

    fields = ['order_id', 'product_id', 'product_qty', 'qty_received', 'product_uom']
    lines = models.execute_kw(db, uid, password,
        'purchase.order.line', 'search_read',
        [domain], {'fields': fields})

    product_data = {}

    for line in lines:
        product_id = line['product_id'][0]
        product_name = line['product_id'][1]
        uom = line['product_uom'][1]

        order = models.execute_kw(db, uid, password,
            'purchase.order', 'read',
            [line['order_id'][0]], {'fields': ['name', 'partner_id', 'date_order']})[0]

        qty_demandada = line['product_qty']
        qty_recepcionada = line['qty_received']
        qty_pendiente = round(qty_demandada - qty_recepcionada, 2)

        if product_id not in product_data:
            product_data[product_id] = {
                'producto': product_name,
                'unidad': uom,
                'cantidad_demandada_total': 0,
                'cantidad_recepcionada_total': 0,
                'cantidad_pendiente_total': 0,
                'ordenes': []
            }

        product_data[product_id]['cantidad_demandada_total'] += qty_demandada
        product_data[product_id]['cantidad_recepcionada_total'] += qty_recepcionada
        product_data[product_id]['cantidad_pendiente_total'] += qty_pendiente

        product_data[product_id]['ordenes'].append({
            'orden_compra': order['name'],
            'proveedor': order['partner_id'][1],
            'fecha_orden': order['date_order'],
            'cantidad_demandada': qty_demandada,
            'cantidad_recepcionada': qty_recepcionada,
            'cantidad_pendiente': qty_pendiente
        })

    return list(product_data.values())
