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
      {raffles.map(r => <RaffleRow key={r.id} r={r} reload={load} />)}
      {!raffles.length && <div className="card">Todavía no creaste rifas. Creá la primera abajo.</div>}
      <CreateRaffle done={load} />
    </div>
  )
}

const CARTEL = 'Para publicar tu rifa debés abonar el servicio de RifaPay. Envía Solicitar autorización y te contactamos para activarla.'
const ESTADOS = { pending: 'Pendiente de autorización', active: 'Activa', paused: 'Pausada', closed: 'Cerrada', rejected: 'Rechazada' }

function CreateRaffle({ done }) {
  const [f, setF] = useState({ title: '', total_numbers: 100, price: '', prizes: '', draw_date: '' })
  return (
    <form className="card flex flex-col gap-2" onSubmit={async (e) => {
      e.preventDefault()
      try {
        await api.post('/api/organizer/raffles', {
          title: f.title, total_numbers: Number(f.total_numbers), price: Number(f.price),
          prizes: f.prizes, draw_date: f.draw_date ? new Date(f.draw_date).toISOString() : null,
        })
        setF({ title: '', total_numbers: 100, price: '', prizes: '', draw_date: '' })
        done()
      } catch (err) { alert(err.response?.data?.detail || 'Error al crear') }
    }}>
      <h3 className="font-semibold">Crear rifa (queda pendiente hasta que el admin la autorice)</h3>
      <input className="input" placeholder="Título" value={f.title} onChange={e => setF({ ...f, title: e.target.value })} required />
      <input className="input" type="number" min="1" max="10000" placeholder="Cantidad de números" value={f.total_numbers} onChange={e => setF({ ...f, total_numbers: e.target.value })} required />
      <input className="input" type="number" step="0.01" min="0.01" placeholder="Precio por número" value={f.price} onChange={e => setF({ ...f, price: e.target.value })} required />
      <input className="input" placeholder="Premios" value={f.prizes} onChange={e => setF({ ...f, prizes: e.target.value })} />
      <input className="input" type="datetime-local" value={f.draw_date} onChange={e => setF({ ...f, draw_date: e.target.value })} required />
      <button className="btn">Crear rifa</button>
    </form>
  )
}

function RaffleRow({ r, reload }) {
  const [orders, setOrders] = useState([])
  const [msg, setMsg] = useState('')
  useEffect(() => {
    const t = localStorage.getItem('token')
    if (!t) return
    api.get(`/api/organizer/raffles/${r.id}/orders`).then(res => setOrders(res.data)).catch(() => {})
  }, [r.id])
  const solicitar = async () => {
    try {
      const { data } = await api.post(`/api/organizer/raffles/${r.id}/request-publication`)
      setMsg(data.message)
      reload()
    } catch (err) { setMsg(err.response?.data?.detail || 'Error') }
  }
  return (
    <div className="card">
      <h3 className="font-semibold">{r.title} - ${r.price} <span className="text-sm text-slate-500">({ESTADOS[r.status] || r.status})</span></h3>
      <p className="text-sm">Vendidos {r.sold_count} | Reservados {r.reserved_count} / {r.total_numbers}</p>
      {r.status === 'pending' && !r.requested && (
        <div className="mt-2 p-3 bg-amber-50 rounded-xl">
          <p className="text-sm">{CARTEL}</p>
          <button className="btn mt-2" onClick={solicitar}>Solicitar autorización para publicar la Rifa</button>
        </div>
      )}
      {r.status === 'pending' && r.requested && (
        <p className="text-sm mt-2 text-amber-700">⏳ Solicitud enviada. Te contactamos para activarla.</p>)}
      {r.status === 'rejected' && (
        <p className="text-sm mt-2 text-red-600">Rechazada: {r.rejection_reason}</p>)}
      {msg && <p className="text-sm mt-2">{msg}</p>}
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
