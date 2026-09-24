import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import api from '../api/client.js'

export default function Checkout() {
  const { id } = useParams()
  const [order, setOrder] = useState(null)

  const load = () => api.get(`/api/orders/${id}`).then(r => setOrder(r.data)).catch(() => {})
  useEffect(() => {
    load()
    const t = setInterval(load, 10000)
    return () => clearInterval(t)
  }, [id])

  if (!order) return <div className="card">Cargando orden...</div>
  const paid = order.status === 'paid'
  const expired = order.status === 'expired'

  if (expired) return (
    <div className="card max-w-xl mx-auto">
      <h2 className="text-xl font-semibold">⏰ Tu reserva expiró</h2>
      <p className="mt-2">{order.notice || 'No se acreditó el pago en 30 minutos y los números volvieron a estar libres.'}</p>
      <p className="text-sm mt-2">Eran los N° <b>{order.numbers.join(', ')}</b> por <b>${order.amount}</b>.</p>
      <a className="btn mt-4 inline-block" href={`/rifa/${order.raffle_id}`}>Elegir números de nuevo</a>
    </div>
  )

  return (
    <div className="card max-w-xl mx-auto">
      <h2 className="text-xl font-semibold">{paid ? '✓ Pagado, tus números son tuyos' : 'Pagá por transferencia'}</h2>
      <p className="mt-2">Números: <b>{order.numbers.join(', ')}</b></p>
      <div className="bg-slate-100 rounded-xl p-4 mt-3">
        <p>Monto exacto: <b className="text-lg">${order.amount}</b></p>
        <p className="text-sm text-red-600">Tiene que ser exacto con centavos, sino no se confirma solo.</p>
        <p className="mt-2">CVU: <b>{order.cvu}</b></p>
        <p>Alias: <b>{order.alias}</b></p>
        <p>Titular: <b>{order.holder}</b></p>
      </div>
      {!paid && (
        <>
          <p className="text-sm mt-3">Estado: <b>{order.status}</b>. Esta página se actualiza sola. Puede tardar hasta 2 horas por el banco.</p>
          <button className="btn mt-3" onClick={() => api.post(`/api/orders/${id}/notified`).then(load)}>Ya transferí, avisar</button>
        </>
      )}
      {paid && <PaidBox order={order} />}
    </div>
  )
}

function PaidBox({ order }) {
  const text = `RifaPay - Pago confirmado\nRifa: ${order.raffle_title || ''}\nNumeros: ${order.numbers.join(', ')}\nMonto: $${order.amount}\nID: ${order.id}`
  const wa = `https://wa.me/?text=${encodeURIComponent(text)}`
  return (
    <div className="mt-4 flex flex-col gap-2">
      <p className="text-sm text-emerald-700">Te enviamos el comprobante por email. Guardá el ID ante cualquier reclamo.</p>
      <div className="flex gap-2">
        <a className="btn" href={wa} target="_blank" rel="noreferrer">Recibir por WhatsApp</a>
        <a className="btn-sec" href={`/rifa/${order.raffle_id}`}>Ver rifa</a>
      </div>
    </div>
  )
}
