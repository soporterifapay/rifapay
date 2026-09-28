import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../api/client.js'
import { Spinner, useAsync, useToast } from '../components/ui.jsx'

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

export default function Login() {
  const nav = useNavigate()
  const toast = useToast()
  const [tab, setTab] = useState('login')
  const [form, setForm] = useState({ email: '', password: '', name: '' })
  const [error, setError] = useState('')

  const submit = async (e) => {
    e.preventDefault()
    setError('')
    if (!EMAIL_RE.test(form.email.trim())) {
      const msg = 'Ingresá un email válido.'
      setError(msg)
      toast(msg, 'error')
      return
    }
    try {
      if (tab === 'login') {
        const { data } = await api.post('/api/organizer/auth/login', {
          email: form.email.trim(), password: form.password })
        localStorage.setItem('token', data.access_token)
        toast('¡Bienvenido!', 'ok')
        nav('/dashboard')
      } else {
        const { data } = await api.post('/api/organizer/auth/register', {
          email: form.email.trim(), password: form.password, name: form.name.trim() || 'Organizador' })
        localStorage.setItem('token', data.access_token)
        toast('Cuenta creada. ¡Bienvenido!', 'ok')
        nav('/dashboard')
      }
    } catch (err) {
      const msg = err.response?.status === 401 ? 'Email o contraseña incorrectos.'
        : err.response?.status === 429 ? 'Demasiados intentos, esperá un minuto.'
        : (typeof err.response?.data?.detail === 'string' ? err.response.data.detail : 'No se pudo entrar.')
      setError(msg)
      toast(msg, 'error')
    }
  }
  const [doAuth, busyAuth] = useAsync(submit)

  return (
    <div className="flex justify-center items-center min-h-[70vh]">
      <div className="card w-full max-w-sm">
        <h2 className="text-xl font-bold text-center">{tab === 'login' ? '🔑 Iniciar sesión' : '📝 Crear cuenta'}</h2>
        <form className="flex flex-col gap-3 mt-4" onSubmit={doAuth} noValidate>
          {tab === 'register' && (
            <label className="text-sm text-slate-600">👤 Nombre
              <input className="input mt-1" maxLength={120} placeholder="Cómo te llamás"
                value={form.name} onChange={e => setForm({ ...form, name: e.target.value })}
                disabled={busyAuth} required />
            </label>
          )}
          <label className="text-sm text-slate-600">📧 Email
            <input className="input mt-1" type="email" maxLength={254} placeholder="vos@email.com"
              value={form.email} onChange={e => setForm({ ...form, email: e.target.value })}
              disabled={busyAuth} required />
          </label>
          <label className="text-sm text-slate-600">🔒 Contraseña
            <input className="input mt-1" type="password" minLength={8} placeholder="Tu contraseña"
              value={form.password} onChange={e => setForm({ ...form, password: e.target.value })}
              disabled={busyAuth} required />
          </label>
          {error && <p className="text-sm text-red-600" role="alert">{error}</p>}
          <button className="btn w-full" disabled={busyAuth} aria-busy={busyAuth}>
            {busyAuth ? <Spinner label={tab === 'login' ? 'Entrando' : 'Creando cuenta'} /> : (tab === 'login' ? '🔑 Iniciar sesión' : '📝 Crear cuenta')}
          </button>
        </form>
        <p className="text-center text-sm mt-4">
          {tab === 'login' ? (
            <>¿No tienes cuenta? <button type="button" onClick={() => { setTab('register'); setError('') }}
              className="text-brand-700 font-semibold underline">Regístrate</button></>
          ) : (
            <>¿Ya tienes cuenta? <button type="button" onClick={() => { setTab('login'); setError('') }}
              className="text-brand-700 font-semibold underline">Entrá</button></>
          )}
        </p>
      </div>
    </div>
  )
}
