import { useEffect, useState } from 'react'
import api from '../api/client.js'
import { LogoMark } from '../components/Logo.jsx'
import { NavButton, ProgressBar, WhatsButton, fmtMoney } from '../components/ui.jsx'

export default function Home() {
  const [items, setItems] = useState(null)
  const [slow, setSlow] = useState(false)
  useEffect(() => {
    const t = setTimeout(() => setSlow(true), 4000)
    api.get('/api/raffles').then(r => setItems(r.data)).catch(() => setItems([]))
      .finally(() => clearTimeout(t))
    return () => clearTimeout(t)
  }, [])
  const scrollToList = () => {
    document.getElementById('lista-rifas')?.scrollIntoView({ behavior: 'smooth' })
  }
  return (
    <>
      <section className="card text-center mb-4" aria-label="Presentación">
        <div className="flex justify-center"><LogoMark variant="ticket" size={56} /></div>
        <p className="text-lg sm:text-xl font-semibold text-slate-600 mt-2">Tus rifas en piloto automático</p>
        <div className="flex gap-2 justify-center mt-4 flex-wrap">
          <button className="btn" onClick={scrollToList}>Ver rifas</button>
          <NavButton to="/login" variant="btn-sec">Crear tu rifa</NavButton>
        </div>
        <ul className="flex gap-4 justify-center mt-4 text-sm text-slate-600 flex-wrap">
          <li>✓ Sin comisiones</li>
          <li>⚡ Confirmación automática</li>
          <li>🔒 Pagos verificados</li>
        </ul>
      </section>
      <div id="lista-rifas">
        <RaffleList items={items} slow={slow} />
      </div>
      <WhatsButton />
    </>
  )
}

function RaffleList({ items, slow }) {
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
          {r.description && <p className="text-sm text-slate-600 mt-1">{r.description}</p>}
          <p className="text-sm text-slate-600">{r.prizes}</p>
          {r.draw_date && <p className="text-sm mt-1">🎰 Sorteo: {new Date(r.draw_date).toLocaleString('es-AR')}</p>}
          <p className="mt-2">Precio por número: <b className="tnum">{fmtMoney(r.price)}</b></p>
          <div className="mt-2"><ProgressBar sold={r.sold_count} total={r.total_numbers} /></div>
          <NavButton to={`/rifa/${r.id}`} className="mt-3">Elegir números</NavButton>
        </div>
      ))}
    </div>
  )
}
