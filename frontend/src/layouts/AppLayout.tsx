import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'

const links = [{ to: '/dashboard', label: 'Dashboard', icon: '▦' }, { to: '/vehicles', label: 'Vehículos', icon: '▤' }]
export function AppLayout() {
  const { user, logout } = useAuth(); const navigate = useNavigate()
  const leave = () => { logout(); navigate('/login') }
  return <div className="min-h-screen bg-slate-50 text-slate-800 md:flex">
    <aside className="bg-slate-950 px-4 py-5 text-slate-100 md:w-64 md:shrink-0">
      <div className="mb-8 flex items-center gap-3 px-2"><span className="grid h-10 w-10 place-items-center rounded-xl bg-cyan-400 font-bold text-slate-950">S</span><div><p className="font-bold tracking-wide">SIGEFLOT WEB</p><p className="text-xs text-slate-400">Gestión de flota</p></div></div>
      <nav className="flex gap-2 md:flex-col">{links.map(link => <NavLink key={link.to} to={link.to} className={({ isActive }) => `flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition ${isActive ? 'bg-cyan-400 text-slate-950' : 'text-slate-300 hover:bg-slate-800 hover:text-white'}`}><span>{link.icon}</span>{link.label}</NavLink>)}</nav>
      <button onClick={leave} className="mt-5 flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-left text-sm text-slate-300 hover:bg-slate-800 hover:text-white md:mt-12">↪ Cerrar sesión</button>
    </aside>
    <div className="min-w-0 flex-1"><header className="flex min-h-18 items-center justify-between border-b border-slate-200 bg-white px-5 py-3 sm:px-8"><div><h1 className="font-bold text-slate-900">SIGEFLOT WEB</h1><p className="hidden text-xs text-slate-500 sm:block">Sistema Integral de Gestión de Flota y Mantenimiento Vehicular</p></div><div className="text-right"><p className="text-sm font-semibold">{user?.nombres} {user?.apellidos}</p><p className="text-xs font-medium tracking-wide text-cyan-700">{user?.rol}</p></div></header><main className="mx-auto max-w-7xl p-5 sm:p-8"><Outlet /></main></div>
  </div>
}
