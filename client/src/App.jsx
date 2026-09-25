import { Suspense, lazy, useEffect, useState } from 'react'
import { Link, Route, Routes, useLocation } from 'react-router-dom'
import api from './api/client.js'
import { ToastHost } from './components/ui.jsx'

const Home = lazy(() => import('./pages/Home.jsx'))
const RaffleDetail = lazy(() => import('./pages/RaffleDetail.jsx'))
const Checkout = lazy(() => import('./pages/Checkout.jsx'))
const Login = lazy(() => import('./pages/Login.jsx'))
const Dashboard = lazy(() => import('./pages/Dashboard.jsx'))
const Admin = lazy(() => import('./pages/Admin.jsx'))

function Shell() {
  const [role, setRole] = useState('')
  const loc = useLocation()
  useEffect(() => {
    if (!localStorage.getItem('token')) { setRole(''); return }
    api.get('/api/organizer/me').then(r => setRole(r.data.role)).catch(() => {})
  }, [loc.pathname])
  return (
    <div className="max-w-5xl mx-auto p-4">
      <header className="flex flex-wrap gap-2 justify-between items-center py-4">
        <Link to="/" className="text-2xl font-bold text-brand-700">RifaPay</Link>
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
