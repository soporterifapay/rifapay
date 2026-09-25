import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import api from '../api/client.js'
import { ProgressBar, TicketGrid, WhatsButton, fmtMoney, useToast } from '../components/ui.jsx'

export default function RaffleDetail() {
  const { id } = useParams()
  const nav = useNavigate()
  const toast = useToast()
  const [raffle, setRaffle] = useState(null)
  const [recent, setRecent] = useState([])
  const [sel, setSel] = useState([])
  const [error, setError] = useState('')
  const [form, setForm] = useState({ buyer_name: '', buyer_phone: '', buyer_dni: '', buyer_email: '' })

  useEffect(() => {
    api.get(`/api/raffles/${id}`).then(r => setRaffle(r.data)).catch(() => setRaffle(false))
    api.get(`/api/raffles/${id}/recent`).then(r => setRecent(r.data)).catch(() => {})
  }, [id])
  if (raffle === null) return <div className="card" aria-busy="true">Cargando...</div>
  if (raffle === false) return <div className="card">Esta rifa no existe o aún no está publicada.</div>

  const toggle = (n, status) => {
    if (status !== 'available') return
    setSel(s => s.includes(n) ? s.filter(x => x !== n) : [...s, n].slice(0, 20))
  }

  const submit = async (e) => {
    e.preventDefault()
    setError('')
    try {
      const { data } = await api.post('/api/orders', { raffle_id: id, numbers: sel, ...form })
      nav(`/orden/${data.id}`)
    } catch (err) {
      const code = err.response?.status
      const detail = err.response?.data?.detail
      const msg = code === 409 ? 'Alguien se llevó uno de esos números. Elegí otros.'
        : code === 429 ? 'Demasiados intentos, esperá un minuto.'
        : code === 404 ? 'La rifa ya no acepta reservas.'
        : (typeof detail === 'string' ? detail : 'No se pudo reservar, probá de nuevo.')
      setError(msg)
      toast(msg, 'error')
    }
  }

  const sold = raffle.tickets.filter(t => t.status === 'sold').length

  return (
    <div className="grid gap-4 md:grid-cols-3">
      <div className="card md:col-span-2">
        <h2 className="text-xl font-semibold">{raffle.title}</h2>
        {raffle.description && <p className="text-sm text-slate-600 mt-1">{raffle.description}</p>}
        <p className="text-sm text-slate-600">Premios: {raffle.prizes}</p>
        {raffle.draw_date && <p className="text-sm mt-1">🎰 Sorteo: {new Date(raffle.draw_date).toLocaleString('es-AR')}</p>}
        <div className="mt-3"><ProgressBar sold={sold} total={raffle.tickets.length} /></div>
        <TicketGrid tickets={raffle.tickets} selected={sel} onToggle={toggle} />
        <div className="flex gap-4 text-sm mt-3">
          <span>🟩 Libre</span><span>🟨 Reservado</span><span>⬜ Pagado</span>
        </div>
        {recent.length > 0 && (
          <p className="text-sm mt-3 text-slate-600">🔥 Últimos vendidos: <b>{recent.flatMap(r => r.numbers).slice(0, 12).join(', ')}</b> <span className="text-slate-400">({recent[0].ago})</span></p>
        )}
      </div>
      <form className="card flex flex-col gap-2" onSubmit={submit}>
        <h3 className="font-semibold">Tus números: {sel.join(', ') || '-'}</h3>
        {sel.length > 0 && <p className="text-sm">Total estimado: <b>{fmtMoney(sel.length * raffle.price)}</b></p>}
        <label className="text-sm">Nombre y apellido
          <input className="input mt-1" maxLength={120} placeholder="Nombre y apellido" value={form.buyer_name} onChange={e => setForm({ ...form, buyer_name: e.target.value })} required />
        </label>
        <label className="text-sm">Email (te enviamos el comprobante)
          <input className="input mt-1" type="email" maxLength={254} value={form.buyer_email} onChange={e => setForm({ ...form, buyer_email: e.target.value })} required />
        </label>
        <label className="text-sm">Teléfono / WhatsApp
          <input className="input mt-1" maxLength={40} placeholder="Teléfono / WhatsApp" value={form.buyer_phone} onChange={e => setForm({ ...form, buyer_phone: e.target.value })} />
        </label>
        <label className="text-sm">DNI (opcional)
          <input className="input mt-1" maxLength={20} placeholder="DNI (opcional)" value={form.buyer_dni} onChange={e => setForm({ ...form, buyer_dni: e.target.value })} />
        </label>
        {error && <p className="text-sm text-red-600" role="alert">{error}</p>}
        <button className="btn" disabled={!sel.length}>Reservar y ver cómo pagar</button>
      </form>
      <WhatsButton />
    </div>
  )
}
