import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import api from '../api/client.js'

export default function Home() {
  const [items, setItems] = useState([])
  useEffect(() => { api.get('/api/raffles').then(r => setItems(r.data)).catch(() => {}) }, [])
  if (!items.length) return <div className="card">No hay rifas activas todavía.</div>
  return (
    <div className="grid gap-4 md:grid-cols-2">
      {items.map(r => (
        <div key={r.id} className="card">
          <h2 className="text-xl font-semibold">{r.title}</h2>
          <p className="text-sm text-slate-600">{r.prizes}</p>
          <p className="mt-2">Precio por número: <b>${r.price}</b></p>
          <p className="text-sm">Vendidos: {r.sold_count} / {r.total_numbers}</p>
          <Link className="btn mt-3 inline-block" to={`/rifa/${r.id}`}>Elegir números</Link>
        </div>
      ))}
    </div>
  )
}
