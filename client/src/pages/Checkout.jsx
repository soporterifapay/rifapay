import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import api from '../api/client.js'
import { Countdown, StatusBadge, fmtMoney } from '../components/ui.jsx'

export default function Checkout() {
  const { id } = useParams()
  const [order, setOrder] = useState(null)

  useEffect(() => {
    let alive = true
    const load = () => api.get(`/api/orders/${id}`).then(r => { if (alive) setOrder(r.data) }).catch(() => {})
    load()
    const t = setInterval(() => {
      setOrder(cur => {
        if (cur && (cur.status === 'paid' || cur.status === 'expired')) { clearInterval(t); return cur }
        load()
        return cur
      })
    }, 10000)
    return () => { alive = false; clearInterval(t) }
  }, [id])

  if (!order) return <div className="card" aria-busy="true">Cargando orden...</div>
  const paid = order.status === 'paid'
  const expired = order.status === 'expired'

  if (expired) return (
    <div className="card max-w-xl mx-auto">
      <h2 className="text-xl font-semibold">⏰ Tu reserva expiró</h2>
      <p className="mt-2">{order.notice || 'No se acreditó el pago en 30 minutos y los números volvieron a estar libres.'}</p>
      <p className="text-sm mt-2">Eran los N° <b>{order.numbers.join(', ')}</b> por <b>{fmtMoney(order.amount)}</b>.</p>
      <a className="btn mt-4 inline-block" href={`/rifa/${order.raffle_id}`}>Elegir números de nuevo</a>
    </div>
  )

  return (
    <div className="card max-w-xl mx-auto">
      <h2 className="text-xl font-semibold">{paid ? '✓ Pagado, tus números son tuyos' : 'Pagá por transferencia'}</h2>
      <p className="mt-2"><StatusBadge status={order.status} /> Números: <b>{order.numbers.join(', ')}</b></p>
      {!paid && <div className="mt-2"><Countdown to={order.expires_at} prefix="Tu reserva vence en" /></div>}
      <div className="bg-slate-100 rounded-xl p-4 mt-3">
        <p>Monto exacto: <b className="text-lg">{fmtMoney(order.amount)}</b></p>
        <p className="text-sm text-red-600">Tiene que ser exacto con centavos, sino no se confirma solo.</p>
        {order.cvu && <p className="mt-2">CVU: <b>{order.cvu}</b></p>}
        {order.alias && <p>Alias: <b>{order.alias}</b></p>}
        {order.holder && <p>Titular: <b>{order.holder}</b></p>}
      </div>
      {!paid && (
        <>
          <p className="text-sm mt-3">Esta página se actualiza sola. Puede tardar hasta 2 horas por el banco.</p>
          <button className="btn mt-3" onClick={() => api.post(`/api/orders/${id}/notified`).catch(() => {})}>Ya transferí, avisar</button>
        </>
      )}
      {paid && <PaidBox order={order} />}
    </div>
  )
}

function PaidBox({ order }) {
  const nums = order.numbers.join(', ')
  const lines = [
    `✅ *PAGO CONFIRMADO*`,
    `🧾 ${order.raffle_title || ''}`,
    ``,
    `👋 Hola ${order.buyer_name || ''}, tus números ya participan del sorteo.`,
    ``,
    `🎟️ *Tus números*`,
    '```' + nums + '```',
    ``,
    `💰 Monto acreditado: *$ ${order.amount}*`,
    `📅 Fecha de pago: ${order.paid_at || ''}`,
    `🆔 ID de orden: \`\`\`${order.id}\`\`\``,
  ]
  if (order.draw_date) lines.push(`🎰 Fecha del sorteo: ${order.draw_date}`)
  if (order.dest) lines.push(`📍 Destino: ${order.dest}`)
  lines.push(
    ``,
    `⚠️ _Conservá el ID de orden ante cualquier reclamo. Constancia de compra RifaPay. No reemplaza el comprobante de tu banco._`,
  )
  const wa = `https://wa.me/?text=${encodeURIComponent(lines.join('\n'))}`
  return (
    <div className="mt-4 flex flex-col gap-2">
      <p className="text-sm text-emerald-700">Te enviamos el comprobante por email. Guardá el ID ante cualquier reclamo.</p>
      <div className="flex gap-2 flex-wrap">
        <a className="btn" href={wa} target="_blank" rel="noreferrer">Recibir comprobante por WhatsApp</a>
        <a className="btn-sec" href={`/rifa/${order.raffle_id}`}>Ver rifa</a>
      </div>
    </div>
  )
}
