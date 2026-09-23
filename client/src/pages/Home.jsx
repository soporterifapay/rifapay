import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import api from '../api/client.js'

export default function Home() {
  const [items, setItems] = useState(null)
  const [slow, setSlow] = useState(false)
  useEffect(() => {
    const t = setTimeout(() => setSlow(true), 4000)
    api.get('/api/raffles').then(r => setItems(r.data)).catch(() => setItems([]))
      .finally(() => clearTimeout(t))
    return () => clearTimeout(t)
  }, [])
  if (items === null) return (
    <div className="grid gap-4 md:grid-cols-2" aria-busy="true" aria-label="Cargando rifas">
      {[0, 1].map(i => (
        <div key={i} className="card animate-pulse">
          <div className="h-6 bg-slate-200 rounded w-2/3" />
          <div className="h-4 bg-slate-200 rounded w-1/2 mt-2" />
          <div className="h-4 bg-slate-200 rounded w-1/3 mt-2" />
        </div>
      ))}
      {slow && <p className="text-sm text-slate-500 md:col-span-2">Tardando más de lo normal (el servidor está despertando, ya viene)...</p>}
    </div>
  )
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
