import { Navigate, Route, Routes } from 'react-router-dom'
import { AuthProvider, useAuth } from './contexts/AuthContext'
import { DashboardPage } from './pages/DashboardPage'
import { LoginPage } from './pages/LoginPage'
import { VehiclesPage } from './pages/VehiclesPage'
import { AppLayout } from './layouts/AppLayout'
import { ExitsPage } from './pages/ExitsPage'
import type { Role } from './types/api'

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { token, loading } = useAuth()
  if (loading) return <main className="grid min-h-screen place-items-center text-slate-600">Cargando sesión…</main>
  return token ? children : <Navigate to="/login" replace />
}

const exitRoles: Role[] = ['ADMINISTRADOR', 'MECANICO', 'CHOFER']

function RoleRoute({ allowedRoles, children }: { allowedRoles: Role[]; children: React.ReactNode }) {
  const { user } = useAuth()
  return user && allowedRoles.includes(user.rol) ? children : <Navigate to="/dashboard" replace />
}

function AppRoutes() {
  const { token } = useAuth()
  return <Routes>
    <Route path="/login" element={token ? <Navigate to="/dashboard" replace /> : <LoginPage />} />
    <Route element={<ProtectedRoute><AppLayout /></ProtectedRoute>}>
      <Route path="/dashboard" element={<DashboardPage />} />
      <Route path="/vehicles" element={<VehiclesPage />} />
      <Route path="/salidas" element={<RoleRoute allowedRoles={exitRoles}><ExitsPage /></RoleRoute>} />
    </Route>
    <Route path="*" element={<Navigate to="/dashboard" replace />} />
  </Routes>
}

export default function App() {
  return <AuthProvider><AppRoutes /></AuthProvider>
}
