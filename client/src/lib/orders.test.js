import test from 'node:test'
import assert from 'node:assert/strict'
import { effectiveStatus, isLiveReservation, splitOrders } from './orders.js'

const NOW = new Date('2026-09-24T20:00:00Z').getTime()
const mk = (status, expires) => ({ id: 'x', status, expires_at: expires })

test('reserva vigente', () => {
  assert.equal(isLiveReservation(mk('reserved', '2026-09-24T20:30:00Z'), NOW), true)
  assert.equal(effectiveStatus(mk('reserved', '2026-09-24T20:30:00Z'), NOW), 'reserved_live')
})

test('reserva vencida con numero libre', () => {
  assert.equal(isLiveReservation(mk('reserved', '2026-09-24T19:00:00Z'), NOW), false)
  assert.equal(effectiveStatus(mk('reserved', '2026-09-24T19:00:00Z'), NOW), 'expired_hold')
  assert.equal(effectiveStatus(mk('receipt_uploaded', '2026-09-24T19:00:00Z'), NOW), 'expired_hold')
})

test('finales no cambian', () => {
  assert.equal(effectiveStatus(mk('paid', null), NOW), 'paid')
  assert.equal(effectiveStatus(mk('expired', null), NOW), 'expired')
})

test('split separa vigentes de historial', () => {
  const { live, history } = splitOrders([
    mk('reserved', '2026-09-24T20:30:00Z'),
    mk('reserved', '2026-09-24T19:00:00Z'),
    { id: 'p', status: 'paid', expires_at: null },
  ], NOW)
  assert.equal(live.length, 1)
  assert.equal(history.length, 2)
  assert.ok(history.every(o => o.effective))
})
