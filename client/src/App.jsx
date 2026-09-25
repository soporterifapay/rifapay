import { Suspense, lazy, useEffect, useState } from 'react'
import { Link, Route, Routes, useLocation } from 'react-router-dom'
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
  const loc = useLocation()
  // vista previa de logo: ?logo=ticket (default: drum)
  const logoVar = new URLSearchParams(loc.search).get('logo') === 'ticket' ? 'ticket' : 'drum'
  useEffect(() => {
    if (!localStorage.getItem('token')) { setRole(''); return }
    api.get('/api/organizer/me').then(r => setRole(r.data.role)).catch(() => {})
  }, [loc.pathname])
  return (
    <div className="max-w-5xl mx-auto p-4">
      <header className="flex flex-wrap gap-2 justify-between items-center py-3 sticky top-0 z-30 bg-slate-50/85 backdrop-blur border-b border-slate-200">
        <Link to="/" aria-label="RifaPay inicio"><Logo variant={logoVar} /></Link>
        <nav className="flex gap-2 items-center flex-wrap">
          {role === 'admin' && <Link className="btn-sec" to="/admin">Admin</Link>}
          {role && <span className="text-xs text-slate-500">{role === 'admin' ? 'Admin' : 'Organizador'}</span>}
          <Link className="btn-sec" to="/login">Soy organizador</Link>
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
