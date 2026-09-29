import { Suspense, lazy, useEffect, useState } from 'react'
import { Link, Route, Routes, useLocation, useNavigate } from 'react-router-dom'
import api from './api/client.js'
import { ToastHost, NavButton } from './components/ui.jsx'
import { Logo } from './components/Logo.jsx'

const Home = lazy(() => import('./pages/Home.jsx'))
const RaffleDetail = lazy(() => import('./pages/RaffleDetail.jsx'))
const Checkout = lazy(() => import('./pages/Checkout.jsx'))
const Login = lazy(() => import('./pages/Login.jsx'))
const Dashboard = lazy(() => import('./pages/Dashboard.jsx'))
const Admin = lazy(() => import('./pages/Admin.jsx'))

function Footer() {
  return (
    <footer className="mt-8 rounded-2xl bg-[#064e3b] text-emerald-100 px-6 py-8">
      <div className="grid gap-6 sm:grid-cols-3">
        <nav aria-label="RifaPay">
          <p className="text-xs font-bold tracking-widest text-emerald-300 mb-3">RIFAPAY</p>
          <ul className="space-y-2 text-sm">
            <li><Link className="hover:text-white" to="/">Inicio</Link></li>
            <li><a className="hover:text-white" href="/#lista-rifas">Ver rifas</a></li>
            <li><a className="hover:text-white" href="/#comparativa">Comparativa 0% comisión</a></li>
            <li><Link className="hover:text-white" to="/login">Crear tu rifa</Link></li>
          </ul>
        </nav>
        <div>
          <p className="text-xs font-bold tracking-widest text-emerald-300 mb-3">CONFIANZA</p>
          <ul className="space-y-2 text-sm">
            <li>✓ 0% comisión, siempre</li>
            <li>⚡ Confirmación automática</li>
            <li>🔒 Sin cookies ni rastreadores</li>
          </ul>
        </div>
        <div>
          <p className="text-xs font-bold tracking-widest text-emerald-300 mb-3">CONTACTO</p>
          <ul className="space-y-2 text-sm">
            <li><a className="hover:text-white" href="https://wa.me/5492615362993" target="_blank" rel="noreferrer">WhatsApp</a></li>
            <li><a className="hover:text-white" href="mailto:soporte.rifapay@gmail.com">soporte.rifapay@gmail.com</a></li>
          </ul>
        </div>
      </div>
      <p className="text-xs text-emerald-200/70 mt-6 pt-4 border-t border-emerald-800">© 2026 RifaPay · Tus rifas en piloto automático. RifaPay es la plataforma tecnológica. Verificá siempre a quién le comprás.</p>
    </footer>
  )
}

function Shell() {
  const [role, setRole] = useState('')
  const [logged, setLogged] = useState(false)
  const loc = useLocation()
  const nav = useNavigate()
  useEffect(() => {
    if (!localStorage.getItem('token')) { setRole(''); setLogged(false); return }
    setLogged(true)
    api.get('/api/organizer/me').then(r => setRole(r.data.role)).catch(() => {})
  }, [loc.pathname])
  const logout = () => {
    localStorage.removeItem('token')
    setRole('')
    setLogged(false)
    nav('/')
  }
  const [busyOut, setBusyOut] = useState(false)
  return (
    <div className="max-w-5xl mx-auto p-4">
      <header className="flex flex-wrap gap-2 justify-between items-center py-3 sticky top-0 z-30 bg-[#faf6ef]/85 backdrop-blur border-b border-slate-200">
        <Link to="/" aria-label="RifaPay inicio"><Logo variant="ticket" /></Link>
        <nav className="flex gap-2 items-center flex-wrap">
          {!logged && loc.pathname !== '/login' && <NavButton to="/login">Iniciar sesión</NavButton>}
          {!logged && loc.pathname === '/login' && <NavButton to="/" variant="btn-sec">Volver al inicio</NavButton>}
          {logged && role === 'admin' && <NavButton to="/admin" variant="btn-sec">Panel Admin</NavButton>}
          {logged && role === 'organizer' && <NavButton to="/dashboard" variant="btn-sec">Mi panel</NavButton>}
          {logged && (
            <button className="btn-sec" disabled={busyOut} aria-busy={busyOut}
              onClick={() => { setBusyOut(true); setTimeout(() => { logout(); setBusyOut(false) }, 350) }}>
              {busyOut ? 'Saliendo...' : 'Cerrar sesión'}
            </button>)}
        </nav>
      </header>
      <Suspense fallback={<div className="card" aria-busy="true">Cargando...</div>}>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/rifa/:id" element={<RaffleDetail />} />
          <Route path="/orden/:id" element={<Checkout />} />
          <Route path="/login" element={<Login />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/admin" element={<Admin />} />
        </Routes>
      </Suspense>
      <Footer />
    </div>
  )
}

export default function App() {
  return (
    <ToastHost>
      <Shell />
    </ToastHost>
  )
}
