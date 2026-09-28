/** Estados reales de orden para paneles: distingue reserva vigente de vencida-liberada.
 *  Puro (sin DOM): testeable con node --test.
 *  Una orden reserved/receipt_uploaded con expires_at pasado = "Vencida - número libre"
 *  (el número ya se liberó, pero la orden sigue buscando pago tardío hasta 24h).
 */

export function isLiveReservation(order, nowMs = Date.now()) {
  if (order.status !== 'reserved' && order.status !== 'receipt_uploaded') return false
  if (!order.expires_at) return true
  return new Date(order.expires_at).getTime() > nowMs
}

export function effectiveStatus(order, nowMs = Date.now()) {
  if (isLiveReservation(order, nowMs)) return 'reserved_live'
  if (order.status === 'reserved' || order.status === 'receipt_uploaded') return 'expired_hold'
  return order.status
}

export const EFFECTIVE_LABEL = {
  reserved_live: 'Reservado',
  expired_hold: 'Vencida - número libre',
  paid: 'Pagado',
  expired: 'Expirado',
  observed: 'Observado',
  receipt_uploaded: 'Reservado',
  reserved: 'Reservado',
}

export function splitOrders(orders, nowMs = Date.now()) {
  const live = []
  const history = []
  for (const o of orders || []) {
    const eff = effectiveStatus(o, nowMs)
    ;(eff === 'reserved_live' ? live : history).push({ ...o, effective: eff })
  }
  return { live, history }
}
