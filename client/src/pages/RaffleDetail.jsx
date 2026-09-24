import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import api from '../api/client.js'

export default function RaffleDetail() {
  const { id } = useParams()
  const nav = useNavigate()
  const [raffle, setRaffle] = useState(null)
  const [sel, setSel] = useState([])
  const [form, setForm] = useState({ buyer_name: '', buyer_phone: '', buyer_dni: '', buyer_email: '' })

  useEffect(() => { api.get(`/api/raffles/${id}`).then(r => setRaffle(r.data)) }, [id])
  if (!raffle) return <div className="card">Cargando...</div>

  const toggle = (n, status) => {
    if (status !== 'available') return
    setSel(s => s.includes(n) ? s.filter(x => x !== n) : [...s, n].slice(0, 20))
  }

  const submit = async (e) => {
    e.preventDefault()
    const { data } = await api.post('/api/orders', { raffle_id: id, numbers: sel, ...form })
    nav(`/orden/${data.id}`)
  }

  return (
    <div className="grid gap-4 md:grid-cols-3">
      <div className="card md:col-span-2">
        <h2 className="text-xl font-semibold">{raffle.title}</h2>
        <div className="grid grid-cols-5 sm:grid-cols-10 gap-2 mt-4">
          {raffle.tickets.map(t => (
            <button key={t.number} aria-label={`numero ${t.number}`}
              onClick={() => toggle(t.number, t.status)}
              className={`rounded-lg p-2 text-sm ${t.status === 'available' ? 'ticket-free' : t.status === 'reserved' ? 'ticket-res' : 'ticket-sold'} ${sel.includes(t.number) ? 'ring-2 ring-emerald-600' : ''}`}>
              {t.number}
            </button>
          ))}
        </div>
        <div className="flex gap-4 text-sm mt-3">
          <span>🟩 Libre</span><span>🟨 Reservado</span><span>⬜ Pagado</span>
        </div>
      </div>
      <form className="card flex flex-col gap-2" onSubmit={submit}>
        <h3 className="font-semibold">Tus números: {sel.join(', ') || '-'}</h3>
        <input className="input" placeholder="Nombre y apellido" value={form.buyer_name} onChange={e => setForm({ ...form, buyer_name: e.target.value })} required />
        <input className="input" type="email" placeholder="Email (te enviamos el comprobante)" value={form.buyer_email} onChange={e => setForm({ ...form, buyer_email: e.target.value })} required />
        <input className="input" placeholder="Teléfono / WhatsApp" value={form.buyer_phone} onChange={e => setForm({ ...form, buyer_phone: e.target.value })} />
        <input className="input" placeholder="DNI (opcional)" value={form.buyer_dni} onChange={e => setForm({ ...form, buyer_dni: e.target.value })} />
        <button className="btn" disabled={!sel.length}>Reservar y ver cómo pagar</button>
      </form>
    </div>
  )
}
