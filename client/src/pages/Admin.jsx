import { useEffect, useState } from 'react'
import api from '../api/client.js'
import { ConfirmModal, StatusBadge, fmtMoney, useToast } from '../components/ui.jsx'

const ESTADOS = { pending: 'Pendiente', active: 'Activa', paused: 'Pausada', closed: 'Cerrada', rejected: 'Rechazada' }

export default function Admin() {
  const [items, setItems] = useState([])
  const [filtro, setFiltro] = useState('')
  const [edit, setEdit] = useState(null)
  const [denied, setDenied] = useState(false)
  const [confirm, setConfirm] = useState(null)
  const [rejectFor, setRejectFor] = useState(null)
  const [reason, setReason] = useState('')
  const toast = useToast()

  useEffect(() => {
    api.get('/api/organizer/me').then(r => {
      if (r.data.role !== 'admin') setDenied(true)
    }).catch(() => setDenied(true))
  }, [])

  if (denied) return <div className="card">Solo admin. Iniciá sesión con una cuenta administradora.</div>

  const load = () => api.get('/api/admin/raffles' + (filtro ? `?status=${filtro}` : ''))
    .then(r => setItems(r.data)).catch(() => {})
  useEffect(load, [filtro])

  const act = (fn, okMsg) => fn
    .then(() => { if (okMsg) toast(okMsg, 'ok'); load() })
    .catch(e => toast(typeof e.response?.data?.detail === 'string' ? e.response.data.detail : 'Error', 'error'))

  return (
    <div className="grid gap-4">
      <div className="card flex gap-2 items-center">
        <h2 className="font-semibold">Administración (rol Admin)</h2>
        <select className="input max-w-xs" value={filtro} onChange={e => setFiltro(e.target.value)}>
          <option value="">Todas</option>
          {Object.entries(ESTADOS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
        </select>
        <button className="btn-sec" onClick={load}>Recargar</button>
      </div>
      {items.map(r => (
        <div key={r.id} className="card">
          <div className="flex justify-between flex-wrap gap-2">
            <div>
              <h3 className="font-semibold">{r.title} <StatusBadge status={r.status} /></h3>
              <p className="text-sm text-slate-600">{r.owner_email} · {fmtMoney(r.price)} · {r.sold}/{r.total_numbers} vendidos
                {r.requested && r.status === 'pending' ? ' · 📩 solicitó publicación' : ''}</p>
              {r.status === 'rejected' && r.rejection_reason && (
                <p className="text-sm text-red-600">Motivo: {r.rejection_reason}</p>)}
            </div>
            <div className="flex gap-2 flex-wrap">
              {(r.status === 'pending' || r.status === 'rejected') && (
                <button className="btn" onClick={() => act(api.post(`/api/admin/raffles/${r.id}/approve`), 'Rifa aprobada y publicada')}>Aprobar</button>)}
              {r.status === 'pending' && (
                <button className="btn-sec" onClick={() => { setRejectFor(r); setReason('') }}>Rechazar</button>)}
              {r.status === 'active' && (
                <button className="btn-sec" onClick={() => act(api.patch(`/api/admin/raffles/${r.id}`, { status: 'paused' }), 'Rifa pausada')}>Pausar</button>)}
              {r.status === 'paused' && (
                <button className="btn" onClick={() => act(api.patch(`/api/admin/raffles/${r.id}`, { status: 'active' }), 'Rifa reanudada')}>Reanudar</button>)}
              {(r.status === 'active' || r.status === 'paused') && (
                <button className="btn-sec" onClick={() => setConfirm({ id: r.id, title: r.title, action: 'closed', label: 'Cerrar', body: 'No aceptará más reservas. El historial se conserva.' })}>Cerrar</button>)}
              <button className="btn-sec" onClick={() => setEdit(edit?.id === r.id ? null : r)}>Editar</button>
              <button className="btn-sec" onClick={() => setConfirm({ id: r.id, title: r.title, action: 'delete', label: 'Eliminar', body: 'Solo si no tiene ventas. Esta acción no se puede deshacer.' })}>Eliminar</button>
            </div>
          </div>
          {edit?.id === r.id && <EditForm r={r} done={() => { setEdit(null); load() }} />}
          <AdminOrders raffleId={r.id} />
        </div>
      ))}
      {!items.length && <div className="card">Sin rifas con ese filtro.</div>}
      <ConfirmModal open={!!confirm} title={`${confirm?.label}: ${confirm?.title}`} body={confirm?.body}
        confirmLabel={confirm?.label}
        onCancel={() => setConfirm(null)}
        onConfirm={() => {
          const c = confirm
          setConfirm(null)
          if (!c) return
          if (c.action === 'delete') act(api.delete(`/api/admin/raffles/${c.id}`), 'Rifa eliminada')
          else act(api.patch(`/api/admin/raffles/${c.id}`, { status: c.action }), 'Listo')
        }} />
      {rejectFor && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4" role="dialog" aria-modal="true" aria-label="Motivo del rechazo">
          <div className="absolute inset-0 bg-black/40" onClick={() => setRejectFor(null)} />
          <form className="card relative max-w-sm w-full flex flex-col gap-2" onSubmit={(e) => {
            e.preventDefault()
            const r = rejectFor
            setRejectFor(null)
            act(api.post(`/api/admin/raffles/${r.id}/reject`, { reason }), 'Rifa rechazada')
          }}>
            <h3 className="font-semibold">Rechazar: {rejectFor.title}</h3>
            <label className="text-sm">Motivo (lo ve el organizador)
              <input className="input mt-1" maxLength={500} value={reason} onChange={e => setReason(e.target.value)} required />
            </label>
            <div className="flex gap-2 justify-end">
              <button type="button" className="btn-sec" onClick={() => setRejectFor(null)}>Cancelar</button>
              <button className="btn-danger">Rechazar</button>
            </div>
          </form>
        </div>
      )}
    </div>
  )
}

function EditForm({ r, done }) {
  const toast = useToast()
  const [f, setF] = useState({ title: r.title, price: r.price, prizes: '', draw_date: '', cvu: '', alias: '', holder: '' })
  return (
    <form className="grid gap-2 mt-3 p-3 bg-slate-50 rounded-xl" onSubmit={async (e) => {
      e.preventDefault()
      const body = {}
      for (const [k, v] of Object.entries(f)) if (v !== '' && v != null) body[k] = k === 'price' ? Number(v) : v
      try {
        await api.patch(`/api/admin/raffles/${r.id}`, body)
        done()
      } catch (err) { toast(typeof err.response?.data?.detail === 'string' ? err.response.data.detail : 'Error', 'error') }
    }}>
      <p className="text-sm font-medium">Editar (admin puede todo; cantidad de números no se cambia)</p>
      <input className="input" placeholder="Título" value={f.title} onChange={e => setF({ ...f, title: e.target.value })} />
      <input className="input" type="number" step="0.01" placeholder="Precio" value={f.price} onChange={e => setF({ ...f, price: e.target.value })} />
      <input className="input" placeholder="Premios" onChange={e => setF({ ...f, prizes: e.target.value })} />
      <input className="input" type="datetime-local" onChange={e => setF({ ...f, draw_date: e.target.value })} />
      <input className="input" placeholder="CVU" onChange={e => setF({ ...f, cvu: e.target.value })} />
      <input className="input" placeholder="Alias" onChange={e => setF({ ...f, alias: e.target.value })} />
      <input className="input" placeholder="Titular" onChange={e => setF({ ...f, holder: e.target.value })} />
      <button className="btn">Guardar</button>
    </form>
  )
}

function AdminOrders({ raffleId }) {
  const [orders, setOrders] = useState([])
  const [filtro, setFiltro] = useState('')
  useEffect(() => {
    api.get(`/api/admin/orders?raffle_id=${raffleId}` + (filtro ? `&status=${filtro}` : ''))
      .then(r => setOrders(r.data)).catch(() => {})
  }, [raffleId, filtro])
  return (
    <div className="mt-2 text-sm">
      <select className="input max-w-xs" value={filtro} onChange={e => setFiltro(e.target.value)}>
        <option value="">Órdenes: todas</option>
        <option value="paid">Pagadas</option>
        <option value="reserved">Reservadas</option>
        <option value="receipt_uploaded">Con comprobante</option>
        <option value="expired">Expiradas</option>
        <option value="observed">Observadas</option>
      </select>
      {orders.map(o => (
        <div key={o.id} className="flex justify-between gap-2 flex-wrap border-b py-1">
          <span>N° {o.numbers.join(',')} - {o.buyer} ({o.email}) - {fmtMoney(o.amount)}</span>
          <StatusBadge status={o.status} />
        </div>
      ))}
    </div>
  )
}
