import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../api/client.js'

export default function Login() {
  const nav = useNavigate()
  const [form, setForm] = useState({ email: 'demo@rifapay.local', password: 'demo1234' })
  return (
    <form className="card max-w-sm mx-auto flex flex-col gap-2" onSubmit={async (e) => {
      e.preventDefault()
      try {
        const { data } = await api.post('/api/organizer/auth/login', form)
        localStorage.setItem('token', data.access_token)
        nav('/dashboard')
      } catch {
        const { data } = await api.post('/api/organizer/auth/register', { ...form, name: 'Demo' })
        localStorage.setItem('token', data.access_token)
        nav('/dashboard')
      }
    }}>
      <h2 className="font-semibold">Entrar como organizador</h2>
      <input className="input" value={form.email} onChange={e => setForm({ ...form, email: e.target.value })} />
      <input className="input" type="password" value={form.password} onChange={e => setForm({ ...form, password: e.target.value })} />
      <button className="btn">Entrar</button>
    </form>
  )
}
