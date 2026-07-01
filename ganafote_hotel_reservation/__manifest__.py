# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Gañafote - Reservas Hoteleras",
    "summary": """Gestión de cupos hoteleros y reservas reutilizando productos,
    variantes y el flujo estándar de ventas de Odoo.""",
    "version": "19.0.1.0.0",
    "description": """
Módulo para Gañafote que permite gestionar cupos de habitaciones cedidas por
hoteles y bloquear disponibilidad al confirmar pedidos de venta.

Principios de diseño:
- Reutiliza res.partner (hotel), product.template/product.product (pernoctación)
  y las variantes estándar para representar características comerciales.
- El presupuesto NO bloquea disponibilidad. El pedido confirmado bloquea.
  El pedido cancelado libera.
- La disponibilidad se calcula por noche (la fecha de salida no consume cupo).

Modelos custom mínimos:
- ganafote.hotel.allotment (cabecera de cupo)
- ganafote.hotel.allotment.line (línea de cupo)
- ganafote.hotel.availability (disponibilidad diaria)

La reserva firme se apoya en el pedido de venta confirmado (sale.order /
sale.order.line) sin tablas intermedias.
""",
    "author": "Xtendoo",
    "company": "Xtendoo",
    "website": "https://xtendoo.es",
    "category": "Sales",
    "depends": [
        "sale_management",
        "product",
    ],
    "license": "AGPL-3",
    "data": [
        "security/ganafote_security.xml",
        "security/ir.model.access.csv",
        "data/ganafote_data.xml",
        "views/product_template_views.xml",
        "views/res_partner_views.xml",
        "views/ganafote_hotel_allotment_views.xml",
        "views/ganafote_hotel_availability_views.xml",
        "views/sale_order_views.xml",
        "views/menus.xml",
    ],
    "demo": [
        "demo/ganafote_demo.xml",
    ],
    "installable": True,
    "application": True,
    "auto_install": False,
}
