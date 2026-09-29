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
  const scrollToCompare = () => {
    document.getElementById('comparativa')?.scrollIntoView({ behavior: 'smooth' })
  }
  return (
    <>
      <section className="card text-center mb-4" aria-label="Presentación">
        <div className="flex justify-center"><LogoMark variant="ticket" size={56} /></div>
        <h1 className="text-2xl sm:text-3xl font-extrabold mt-2">Sin comisiones: todo lo recaudado es tuyo</h1>
        <p className="text-lg sm:text-xl font-semibold text-slate-600 mt-1">Tus rifas en piloto automático</p>
        <p className="text-sm text-slate-600 mt-1">Rifas online: cobrás por transferencia directa a tu cuenta de Mercado Pago, con confirmación automática.</p>
        <div className="flex gap-2 justify-center mt-4 flex-wrap">
          <button className="btn" onClick={scrollToList}>Ver rifas</button>
          <NavButton to="/login" variant="btn-sec">Crear tu rifa</NavButton>
        </div>
        <ul className="flex gap-4 justify-center mt-4 text-sm text-slate-600 flex-wrap">
          <li>✓ Dinero directo a tu cuenta de Mercado Pago</li>
          <li>⚡ Confirmación automática</li>
          <li>🔒 Pagos verificados</li>
        </ul>
        <button className="text-sm text-emerald-700 underline mt-3" onClick={scrollToCompare}>Ver comparativa ↓</button>
      </section>
      <div id="lista-rifas">
        <RaffleList items={items} slow={slow} />
      </div>
      <section id="comparativa" className="card mt-4" aria-label="Comparativa de comisiones">
        <h2 className="text-xl font-bold text-center">¿Cuánto te queda de lo que recaudás?</h2>
        <div className="overflow-x-auto mt-3">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-slate-600">
                <th className="py-2 pr-2 font-medium">Concepto</th>
                <th className="py-2 pr-2 font-medium">Otras plataformas</th>
                <th className="py-2 font-medium">RifaPay</th>
              </tr>
            </thead>
            <tbody>
              <tr className="border-t border-slate-200">
                <td className="py-2 pr-2">Comisión de la plataforma</td>
                <td className="py-2 pr-2 tnum">5%</td>
                <td className="py-2 font-bold text-emerald-700 tnum">0%</td>
              </tr>
              <tr className="border-t border-slate-200">
                <td className="py-2 pr-2">Costo del procesador (tarjeta)</td>
                <td className="py-2 pr-2 tnum">~6–8%</td>
                <td className="py-2 font-bold text-emerald-700 tnum">$0 (transferencia directa)</td>
              </tr>
              <tr className="border-t border-slate-200">
                <td className="py-2 pr-2 font-semibold">De cada $100.000 te quedan</td>
                <td className="py-2 pr-2 tnum">~$87.000</td>
                <td className="py-2 font-bold text-emerald-700 tnum">$100.000</td>
              </tr>
            </tbody>
          </table>
        </div>
        <p className="text-xs text-slate-500 mt-2">RifaPay no cobra comisión ni intermediarios: el dinero va directo a tu cuenta de Mercado Pago.</p>
      </section>
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
