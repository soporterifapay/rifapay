import { Suspense, lazy, useEffect, useState } from 'react'
import { Link, Route, Routes, useLocation, useNavigate } from 'react-router-dom'
import api from './api/client.js'
import { ToastHost } from './components/ui.jsx'
import { Logo } from './components/Logo.jsx'

const Home = lazy(() => import('./pages/Home.jsx'))
const RaffleDetail = lazy(() => import('./pages/RaffleDetail.jsx'))
const Checkout = lazy(() => import('./pages/Checkout.jsx'))
const Login = lazy(() => import('./pages/Login.jsx'))
const Dashboard = lazy(() => import('./pages/Dashboard.jsx'))
const Admin = lazy(() => import('./pages/Admin.jsx'))

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
  return (
    <div className="max-w-5xl mx-auto p-4">
      <header className="flex flex-wrap gap-2 justify-between items-center py-3 sticky top-0 z-30 bg-slate-50/85 backdrop-blur border-b border-slate-200">
        <Link to="/" aria-label="RifaPay inicio"><Logo variant="ticket" /></Link>
        <nav className="flex gap-2 items-center flex-wrap">
          {!logged && <Link className="btn" to="/login">Iniciar sesión</Link>}
          {logged && role === 'admin' && <Link className="btn-sec" to="/admin">Panel Admin</Link>}
          {logged && role === 'organizer' && <Link className="btn-sec" to="/dashboard">Mi panel</Link>}
          {logged && <button className="btn-sec" onClick={logout}>Cerrar sesión</button>}
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
