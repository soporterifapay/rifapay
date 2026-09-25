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
  const [open, setOpen] = useState(false)
  const [nombre, setNombre] = useState('')
  const [mensaje, setMensaje] = useState('')
  const [error, setError] = useState('')
  const toast = useToast()
  const num = '5492615362993'

  const enviar = () => {
    if (!nombre.trim() || !mensaje.trim()) {
      setError('Completá todos los campos')
      return
    }
    const texto = `Hola RifaPay, soy ${nombre.trim()}. ${mensaje.trim()}`
    window.open(`https://wa.me/${num}?text=${encodeURIComponent(texto)}`, '_blank')
    setOpen(false)
    setNombre('')
    setMensaje('')
    setError('')
  }

  return (
    <>
      {open && (
        <div className="fixed bottom-24 right-4 sm:right-6 z-50 w-[min(92vw,21rem)]" role="dialog" aria-modal="true" aria-label="Chat de ayuda por WhatsApp">
          <div className="card !p-0 overflow-hidden">
            <div className="flex justify-between items-center px-5 py-4 text-white" style={{ background: 'linear-gradient(135deg, #25d366, #128c7e)' }}>
              <h4 className="font-bold">💬 RifaPay Soporte</h4>
              <button className="text-xl leading-none opacity-80 hover:opacity-100" onClick={() => setOpen(false)} aria-label="Cerrar chat">×</button>
            </div>
            <div className="p-5">
              <p className="text-sm text-slate-600 bg-slate-100 rounded-xl rounded-tl-sm px-4 py-3 mb-4">
                Hola! Bienvenido a <strong className="text-brand-700">RifaPay</strong>. ¿En qué podemos ayudarte?
              </p>
              <label className="text-xs font-semibold text-slate-500">Tu nombre *
                <input className="input mt-1" maxLength={80} value={nombre} onChange={e => setNombre(e.target.value)} placeholder="Cómo te llamás" />
              </label>
              <label className="text-xs font-semibold text-slate-500 mt-2 block">Mensaje *
                <textarea className="input mt-1" rows={3} maxLength={500} value={mensaje} onChange={e => setMensaje(e.target.value)} placeholder="¿En qué podemos ayudarte?" />
              </label>
              {error && <p className="text-sm text-red-600 mt-2" role="alert">{error}</p>}
              <button className="btn w-full mt-3 !bg-[#25d366] hover:!bg-[#128c7e]" onClick={enviar}>Enviar por WhatsApp</button>
            </div>
          </div>
        </div>
      )}
      <button onClick={() => { setOpen(o => !o); setError('') }}
        aria-label="Abrir chat de ayuda por WhatsApp"
        className="wa-pulse fixed bottom-4 right-4 sm:bottom-6 sm:right-6 z-40 w-[52px] h-[52px] sm:w-[60px] sm:h-[60px] rounded-full flex items-center justify-center hover:scale-105 transition-transform group"
        style={{ backgroundColor: '#25D366', boxShadow: '0 4px 15px rgba(37, 211, 102, 0.4)' }}>
        <span className="hidden sm:block absolute right-[70px] top-1/2 -translate-y-1/2 bg-white text-slate-700 px-3 py-1.5 rounded-lg text-[13px] font-semibold whitespace-nowrap shadow-card opacity-0 pointer-events-none group-hover:opacity-100 group-hover:-translate-x-1 transition-all">
          ¿Necesitás ayuda? Chateá con nosotros
        </span>
        <svg viewBox="0 0 24 24" className="w-[26px] h-[26px] sm:w-8 sm:h-8 fill-white relative z-[2]" aria-hidden="true">
          <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z" />
        </svg>
      </button>
    </>
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
