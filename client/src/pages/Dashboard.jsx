import { useEffect, useState } from 'react'
import api from '../api/client.js'

export default function Dashboard() {
  const [raffles, setRaffles] = useState([])
  const [mp, setMp] = useState({ status: 'disconnected' })

  const load = () => {
    api.get('/api/organizer/raffles').then(r => setRaffles(r.data)).catch(() => {})
    api.get('/api/mp/status').then(r => setMp(r.data)).catch(() => {})
  }
  useEffect(load, [])

  const connect = async () => {
    const { data } = await api.get('/api/mp/authorize-url')
    window.location.href = data.url.startsWith('/api') ? `http://localhost:8000${data.url}` : data.url
  }

  const [form, setForm] = useState({ cvu: '', alias: '', holder: '' })
  const [saved, setSaved] = useState('')

  const savePayout = async (e) => {
    e.preventDefault()
    await api.patch('/api/organizer/account/payout', form)
    setSaved('Guardado ✓')
    setForm({ cvu: '', alias: '', holder: '' })
    load()
    setTimeout(() => setSaved(''), 3000)
  }

  return (
    <div className="grid gap-4">
      <div className="card">
        <h2 className="font-semibold">Tu cuenta de cobro</h2>
        <p className="text-sm">Estado: <b>{mp.status}</b> ({mp.mode === 'real' ? 'cuenta real' : 'simulada'}) {mp.alias && `- ${mp.alias} (${mp.cvu})`}</p>
        {mp.status !== 'connected'
          ? <button className="btn mt-2" onClick={connect}>Conectar mi Mercado Pago</button>
          : <button className="btn-sec mt-2" onClick={() => api.post('/api/mp/disconnect').then(load)}>Desconectar</button>}
        {mp.status === 'connected' && (
          <form className="flex flex-col gap-2 mt-3" onSubmit={savePayout}>
            <p className="text-sm font-medium">Tus datos para cobrar (los ve el comprador):</p>
            <input className="input" placeholder={`CVU actual: ${mp.cvu || '-'}`} value={form.cvu} onChange={e => setForm({ ...form, cvu: e.target.value })} />
            <input className="input" placeholder={`Alias actual: ${mp.alias || '-'}`} value={form.alias} onChange={e => setForm({ ...form, alias: e.target.value })} />
            <input className="input" placeholder={`Titular actual: ${mp.holder || '-'}`} value={form.holder} onChange={e => setForm({ ...form, holder: e.target.value })} />
            <div className="flex gap-2 items-center">
              <button className="btn">Guardar datos</button>
              {saved && <span className="text-sm text-emerald-700">{saved}</span>}
            </div>
          </form>
        )}
        <p className="text-xs text-slate-500 mt-2">Solo miramos si entra plata para confirmar números. No movemos plata.</p>
      </div>
      {raffles.map(r => <RaffleRow key={r.id} r={r} />)}
      {!raffles.length && <div className="card">Todavía no creaste rifas. La demo se crea con el seed.</div>}
    </div>
  )
}

function RaffleRow({ r }) {
  const [orders, setOrders] = useState([])
  useEffect(() => {
    const t = localStorage.getItem('token')
    if (!t) return
    import('../api/client.js').then(({ default: api }) =>
      api.get(`/api/organizer/raffles/${r.id}/orders`).then(res => setOrders(res.data)).catch(() => {}))
  }, [r.id])
  return (
    <div className="card">
      <h3 className="font-semibold">{r.title} - ${r.price}</h3>
      <p className="text-sm">Vendidos {r.sold_count} | Reservados {r.reserved_count} / {r.total_numbers}</p>
      <div className="mt-2 text-sm">
        {orders.map(o => (
          <div key={o.id} className="flex justify-between border-b py-1">
            <span>N° {o.numbers.join(',')} - {o.buyer} - ${o.amount}</span>
            <b>{o.status === 'paid' ? '✓ Pagado' : o.status}</b>
          </div>
        ))}
      </div>
    </div>
  )
}
