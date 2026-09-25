import { createContext, useCallback, useContext, useEffect, useState } from 'react'

const Ctx = createContext(() => {})
export const useToast = () => useContext(Ctx)

export function ToastHost({ children }) {
  const [items, setItems] = useState([])
  const push = useCallback((text, kind = 'info') => {
    const id = Math.random().toString(36).slice(2)
    setItems(s => [...s, { id, text, kind }])
    setTimeout(() => setItems(s => s.filter(x => x.id !== id)), 4500)
  }, [])
  return (
    <Ctx.Provider value={push}>
      {children}
      <div className="fixed bottom-4 left-1/2 -translate-x-1/2 z-50 flex flex-col gap-2 w-[min(92vw,28rem)]" role="status" aria-live="polite">
        {items.map(t => (
          <div key={t.id} className={`rounded-xl px-4 py-2.5 text-sm shadow-card text-white ${t.kind === 'error' ? 'bg-red-600' : t.kind === 'ok' ? 'bg-brand-600' : 'bg-slate-800'}`}>
            {t.text}
          </div>
        ))}
      </div>
    </Ctx.Provider>
  )
}

export function fmtMoney(n) {
  try {
    return new Intl.NumberFormat('es-AR', { style: 'currency', currency: 'ARS', maximumFractionDigits: 2 }).format(n)
  } catch {
    return `$ ${n}`
  }
}

export function StatusBadge({ status }) {
  const map = {
    available: ['Libre', 'badge-ok'], reserved: ['Reservado', 'badge-warn'], sold: ['Pagado', 'badge-mut'],
    paid: ['Pagado', 'badge-ok'], receipt_uploaded: ['Comprobante enviado', 'badge-warn'],
    expired: ['Expirado', 'badge-mut'], observed: ['Observado', 'badge-bad'],
    pending: ['Pendiente', 'badge-warn'], active: ['Activa', 'badge-ok'], paused: ['Pausada', 'badge-warn'],
    closed: ['Cerrada', 'badge-mut'], rejected: ['Rechazada', 'badge-bad'],
  }
  const [label, cls] = map[status] || [status, 'badge-mut']
  return <span className={`badge ${cls}`}>{label}</span>
}

export function ProgressBar({ sold, total }) {
  const pct = total ? Math.min(100, Math.round((sold / total) * 100)) : 0
  return (
    <div>
      <div className="h-2.5 rounded-pill bg-slate-200" role="progressbar" aria-valuenow={pct} aria-valuemin="0" aria-valuemax="100" aria-label={`${pct}% vendido`}>
        <div className="h-2.5 rounded-pill bg-brand-600 transition-all" style={{ width: `${pct}%` }} />
      </div>
      <p className="text-xs text-slate-500 mt-1">{pct}% vendido ({sold}/{total})</p>
    </div>
  )
}

export function useCountdown(targetIso) {
  const [now, setNow] = useState(() => Date.now())
  useEffect(() => {
    const t = setInterval(() => setNow(Date.now()), 1000)
    return () => clearInterval(t)
  }, [])
  if (!targetIso) return null
  const ms = new Date(targetIso).getTime() - now
  if (Number.isNaN(ms) || ms <= 0) return '00:00'
  const m = Math.floor(ms / 60000)
  const s = Math.floor((ms % 60000) / 1000)
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
}

export function Countdown({ to, prefix = 'Te quedan' }) {
  const left = useCountdown(to)
  if (!left) return null
  return <p className="text-sm font-semibold text-amber-700" aria-live="polite">{prefix} {left}</p>
}

const PAGE = 100

export function TicketGrid({ tickets, selected, onToggle }) {
  const [page, setPage] = useState(0)
  const pages = Math.max(1, Math.ceil(tickets.length / PAGE))
  const slice = tickets.slice(page * PAGE, (page + 1) * PAGE)
  return (
    <div>
      <div className="grid grid-cols-5 sm:grid-cols-10 gap-2 mt-4">
        {slice.map(t => (
          <button key={t.number} type="button"
            aria-label={`numero ${t.number}, ${t.status === 'available' ? 'libre' : t.status === 'reserved' ? 'reservado' : 'pagado'}`}
            aria-disabled={t.status !== 'available'}
            disabled={t.status !== 'available'}
            onClick={() => onToggle(t.number, t.status)}
            className={`ticket ${t.status === 'available' ? 'ticket-free' : t.status === 'reserved' ? 'ticket-res' : 'ticket-sold'} ${selected.includes(t.number) ? 'ring-2 ring-brand-600' : ''}`}>
            {t.number}
          </button>
        ))}
      </div>
      {pages > 1 && (
        <div className="flex items-center gap-2 mt-3 text-sm">
          <button type="button" className="btn-sec" disabled={page === 0} onClick={() => setPage(p => p - 1)}>← Anteriores</button>
          <span aria-live="polite">Página {page + 1} de {pages} (números {page * PAGE + 1}–{Math.min(tickets.length, (page + 1) * PAGE)})</span>
          <button type="button" className="btn-sec" disabled={page + 1 >= pages} onClick={() => setPage(p => p + 1)}>Siguientes →</button>
        </div>
      )}
    </div>
  )
}

export function WhatsButton() {
  const num = '5492615362993'
  const text = encodeURIComponent('Hola, tengo una consulta sobre las rifas de RifaPay.')
  return (
    <a href={`https://wa.me/${num}?text=${text}`} target="_blank" rel="noreferrer"
      aria-label="Consultar por WhatsApp"
      className="fixed bottom-4 right-4 z-40 w-14 h-14 rounded-full shadow-card flex items-center justify-center hover:scale-105 transition-transform"
      style={{ backgroundColor: '#25D366' }}>
      <svg viewBox="0 0 32 32" className="w-7 h-7 fill-white" aria-hidden="true">
        <path d="M16 3C9.4 3 4 8.4 4 15c0 2.4.7 4.6 2 6.5L4 29l7.7-2c1.8 1 3.9 1.5 4.3 1.5 6.6 0 12-5.4 12-12S22.6 3 16 3zm0 21.8c-1.4 0-2.8-.4-4-1.1l-.3-.2-4.6 1.2 1.2-4.4-.2-.3c-.8-1.3-1.2-2.7-1.2-4.2 0-4.9 4-8.8 8.9-8.8s8.9 4 8.9 8.9-4 8.9-8.7 8.9zm4.9-6.7c-.3-.1-1.6-.8-1.8-.9-.2-.1-.4-.1-.6.1-.2.3-.7.9-.8 1-.1.2-.3.2-.5.1-.3-.1-1.1-.4-2-1.3-.7-.7-1.2-1.5-1.4-1.7-.1-.2 0-.4.1-.5l.8-.9c.2-.2.2-.4.1-.6l-.8-2c-.2-.5-.4-.4-.6-.4h-.5c-.2 0-.5.2-.7.6-.2.5-.9 2.2-.9 2.2s-.7 1.6.1 3.2c.8 1.7 2.3 3 2.6 3.2.3.2 2.1 1.4 4.5.6.6-.2 1.7-.7 1.9-1.4.2-.6.2-1.2.2-1.3-.1-.1-.3-.2-.6-.3z" />
      </svg>
    </a>
  )
}

export function ConfirmModal({ open, title, body, confirmLabel = 'Confirmar', onConfirm, onCancel }) {
  if (!open) return null
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4" role="dialog" aria-modal="true" aria-label={title}>
      <div className="absolute inset-0 bg-black/40" onClick={onCancel} />
      <div className="card relative max-w-sm w-full">
        <h3 className="font-semibold">{title}</h3>
        {body && <p className="text-sm mt-2">{body}</p>}
        <div className="flex gap-2 mt-4 justify-end">
          <button className="btn-sec" onClick={onCancel}>Cancelar</button>
          <button className="btn-danger" onClick={onConfirm}>{confirmLabel}</button>
        </div>
      </div>
    </div>
  )
}
