import { Link, Route, Routes } from 'react-router-dom'
import Home from './pages/Home.jsx'
import RaffleDetail from './pages/RaffleDetail.jsx'
import Checkout from './pages/Checkout.jsx'
import Login from './pages/Login.jsx'
import Dashboard from './pages/Dashboard.jsx'

export default function App() {
  return (
    <div className="max-w-5xl mx-auto p-4">
      <header className="flex justify-between items-center py-4">
        <Link to="/" className="text-2xl font-bold text-emerald-700">RifaPay</Link>
        <nav className="flex gap-2">
          <Link className="btn-sec" to="/login">Soy organizador</Link>
        </nav>
      </header>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/rifa/:id" element={<RaffleDetail />} />
        <Route path="/orden/:id" element={<Checkout />} />
        <Route path="/login" element={<Login />} />
        <Route path="/dashboard" element={<Dashboard />} />
      </Routes>
    </div>
  )
}
