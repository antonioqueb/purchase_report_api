import os
import xmlrpc.client

url = os.getenv("ODOO_URL")
db = os.getenv("ODOO_DB")
user = os.getenv("ODOO_USER")
password = os.getenv("ODOO_PASSWORD")


def get_connection():
    try:
        common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
        uid = common.authenticate(db, user, password, {})
        if not uid:
            raise Exception("Autenticación fallida con Odoo: UID inválido")
        models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object")
        return uid, models
    except Exception as e:
        raise ConnectionError(f"No se pudo conectar a Odoo: {str(e)}")


def get_partial_and_unreceived_purchase_lines(start_date: str, end_date: str):
    try:
        uid, models = get_connection()

        # 1. Buscar ID de la categoría padre "Materias Primas"
        parent_category_ids = models.execute_kw(db, uid, password,
            'product.category', 'search',
            [[('name', '=', 'Materias Primas')]])

        if not parent_category_ids:
            return []

        parent_id = parent_category_ids[0]

        # 2. Obtener IDs de todas las subcategorías
        all_category_ids = models.execute_kw(db, uid, password,
            'product.category', 'search',
            [[('parent_path', 'ilike', f'{parent_id}/')]])
        all_category_ids.append(parent_id)

        # 3. Buscar líneas de orden de compra en rango de fechas
        domain = [
            ('state', 'in', ['purchase', 'done']),
            ('order_id.date_order', '>=', start_date),
            ('order_id.date_order', '<=', end_date)
        ]

        fields = ['order_id', 'product_id', 'product_qty', 'qty_received', 'product_uom']
        lines = models.execute_kw(db, uid, password,
            'purchase.order.line', 'search_read',
            [domain], {'fields': fields})

        product_data = {}

        for line in lines:
            qty_demandada = line['product_qty']
            qty_recepcionada = line['qty_received']
            if qty_recepcionada >= qty_demandada:
                continue

            product_id = line['product_id'][0]
            product_name = line['product_id'][1]

            # Leer categoría del producto
            product_info = models.execute_kw(db, uid, password,
                'product.product', 'read',
                [product_id], {'fields': ['categ_id']})[0]

            product_category_id = product_info['categ_id'][0]
            if product_category_id not in all_category_ids:
                continue

            uom = line['product_uom'][1]

            # Leer información completa de la orden incluyendo planta y comprador
            order = models.execute_kw(db, uid, password,
                'purchase.order', 'read',
                [line['order_id'][0]],
                {'fields': ['name', 'partner_id', 'date_order', 'user_id', 'planta']})[0]

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
                'comprador': order['user_id'][1] if order['user_id'] else None,
                'planta': order['planta'][1] if order['planta'] else None,
                'cantidad_demandada': qty_demandada,
                'cantidad_recepcionada': qty_recepcionada,
                'cantidad_pendiente': qty_pendiente
            })

        return list(product_data.values())

    except Exception as e:
        # Puedes loguear esto o devolverlo a la vista según lo manejes
        raise RuntimeError(f"Error obteniendo líneas de compra: {str(e)}")
