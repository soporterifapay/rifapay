import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../api/client.js'
import { useToast } from '../components/ui.jsx'

export default function Login() {
  const nav = useNavigate()
  const toast = useToast()
  const [tab, setTab] = useState('login')
  const [form, setForm] = useState({ email: '', password: '', name: '' })
  const [error, setError] = useState('')

  const submit = async (e) => {
    e.preventDefault()
    setError('')
    try {
      if (tab === 'login') {
        const { data } = await api.post('/api/organizer/auth/login', {
          email: form.email, password: form.password })
        localStorage.setItem('token', data.access_token)
        nav('/dashboard')
      } else {
        const { data } = await api.post('/api/organizer/auth/register', {
          email: form.email, password: form.password, name: form.name || 'Organizador' })
        localStorage.setItem('token', data.access_token)
        toast('Cuenta creada. Si tu email es admin, ya tenés acceso total.', 'ok')
        nav('/dashboard')
      }
    } catch (err) {
      const msg = err.response?.status === 401 ? 'Email o contraseña incorrectos.'
        : err.response?.status === 429 ? 'Demasiados intentos, esperá un minuto.'
        : (typeof err.response?.data?.detail === 'string' ? err.response.data.detail : 'No se pudo entrar.')
      setError(msg)
    }
  }

  return (
    <form className="card max-w-sm mx-auto flex flex-col gap-2" onSubmit={submit}>
      <div className="flex gap-2">
        <button type="button" className={tab === 'login' ? 'btn' : 'btn-sec'} onClick={() => setTab('login')}>Entrar</button>
        <button type="button" className={tab === 'register' ? 'btn' : 'btn-sec'} onClick={() => setTab('register')}>Crear cuenta</button>
      </div>
      <h2 className="font-semibold">{tab === 'login' ? 'Entrar como organizador' : 'Crear cuenta de organizador'}</h2>
      {tab === 'register' && (
        <input className="input" maxLength={120} placeholder="Tu nombre (ej: Juan Pérez)" value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} />
      )}
      <input className="input" type="email" maxLength={254} placeholder="Email (ej: vos@email.com)" value={form.email} onChange={e => setForm({ ...form, email: e.target.value })} required />
      <input className="input" type="password" minLength={8} placeholder="Contraseña (mínimo 8 caracteres)" value={form.password} onChange={e => setForm({ ...form, password: e.target.value })} required />
      {error && <p className="text-sm text-red-600" role="alert">{error}</p>}
      <button className="btn">{tab === 'login' ? 'Entrar' : 'Crear cuenta'}</button>
    </form>
  )
}
