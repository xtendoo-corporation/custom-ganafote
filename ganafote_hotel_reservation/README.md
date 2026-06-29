# Gañafote - Reservas Hoteleras

Módulo para gestionar **cupos hoteleros** y **reservas** reutilizando al máximo los
modelos estándar de Odoo (`res.partner`, `product.template`, `product.product`,
`product.attribute`, `sale.order`, `sale.order.line`) y el flujo estándar de
ventas/facturación.

## Concepto

- El **hotel** es un contacto/proveedor (`res.partner`).
- La **pernoctación** es un producto de tipo servicio (`product.template`) marcado como
  *Producto hotelero* y asociado a un hotel.
- Las **características comerciales** (doble, individual, vista mar, media pensión...) se
  modelan con **variantes estándar** de Odoo (`product.attribute`).

## Flujo funcional

1. **Crear el producto hotelero**: marca *Producto hotelero* y asigna el hotel. Añade las
   variantes que afecten al precio/cupo.
2. **Crear un cupo** (`Reservas Hoteleras > Cupos hoteleros`): hotel, fechas y líneas por
   variante con la cantidad cedida, coste por noche y margen. El precio de venta sugerido
   se calcula automáticamente (porcentaje o importe fijo) y es editable.
3. **Confirmar el cupo**: genera la **disponibilidad diaria por noche** (la fecha de
   salida no consume cupo) y bloquea solapamientos con otros cupos confirmados de la misma
   variante.
4. **Presupuesto de venta**: añade líneas con producto hotelero, fechas de entrada/salida
   y número de habitaciones. El sistema calcula noches, fija la cantidad facturable
   (`habitaciones × noches`) y muestra disponibilidad **orientativa**. *No* bloquea cupo.
5. **Confirmar el pedido**: valida la disponibilidad real noche a noche. Si hay cupo,
   crea la **reserva/bloqueo** y descuenta disponibilidad. Si no, impide la confirmación
   con un mensaje claro.
6. **Cancelar el pedido**: cancela la reserva y libera la disponibilidad. Si hay facturas
   o anticipos, avisa de que la regularización contable debe revisarse manualmente.

## Regla del MVP

> Presupuesto no bloquea. Pedido confirmado bloquea. Pedido cancelado libera.

El código está organizado (servicio de disponibilidad en `ganafote.hotel.availability`)
para poder cambiar más adelante el momento de bloqueo (señal, pago total, bloqueo manual).

## Modelos

| Modelo | Propósito |
| --- | --- |
| `ganafote.hotel.allotment` | Cabecera de cupo hotelero |
| `ganafote.hotel.allotment.line` | Línea de cupo (variante, tramo, coste, margen) |
| `ganafote.hotel.availability` | Disponibilidad diaria por noche |

La **reserva/bloqueo** no usa modelos propios: la reserva firme es el `sale.order`
confirmado y la línea hotelera (`sale.order.line`, extendida con
`checkin_date`, `checkout_date`, `nights`, `room_qty`, `allotment_id`,
`hotel_blocked`) guarda la trazabilidad y el consumo de cupo.

## Seguridad

- **Usuario reservas hoteleras**: lee cupos/disponibilidad/reservas y crea reservas al
  confirmar pedidos de venta.
- **Responsable reservas hoteleras**: crea/modifica/confirma/cancela cupos.

## Limitaciones conocidas (pendientes de validar con cliente)

- Momento de la reserva firme (confirmación vs. señal vs. pago total vs. manual).
- Política de anticipos y de cancelación.
- Rooming list, paquetes cerrados vs. noches libres, bloqueos manuales.
- Facturación del cupo completo vs. solo habitaciones vendidas.
- Importación de cupos desde Excel.
