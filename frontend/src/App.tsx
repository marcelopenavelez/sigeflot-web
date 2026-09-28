import { Navigate, Route, Routes } from 'react-router-dom'
import { AuthProvider, useAuth } from './contexts/AuthContext'
import { DashboardPage } from './pages/DashboardPage'
import { LoginPage } from './pages/LoginPage'
import { VehiclesPage } from './pages/VehiclesPage'
import { AppLayout } from './layouts/AppLayout'
import { ExitsPage } from './pages/ExitsPage'
import { NewOrderPage } from './pages/NewOrderPage'
import { OrdersPage } from './pages/OrdersPage'
import { OrderDetailPage } from './pages/OrderDetailPage'
import { EditOrderPage } from './pages/EditOrderPage'
import type { Role } from './types/api'

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { token, loading } = useAuth()
  if (loading) return <main className="grid min-h-screen place-items-center text-slate-600">Cargando sesión…</main>
  return token ? children : <Navigate to="/login" replace />
}

const exitRoles: Role[] = ['ADMINISTRADOR', 'MECANICO', 'CHOFER']
const orderRoles: Role[] = ['ADMINISTRADOR', 'MECANICO']
const orderReadRoles: Role[] = ['ADMINISTRADOR', 'MECANICO', 'CONSULTA']

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
      <Route path="/ordenes/nueva" element={<RoleRoute allowedRoles={orderRoles}><NewOrderPage /></RoleRoute>} />
      <Route path="/ordenes" element={<RoleRoute allowedRoles={orderReadRoles}><OrdersPage /></RoleRoute>} />
      <Route path="/ordenes/:id" element={<RoleRoute allowedRoles={orderReadRoles}><OrderDetailPage /></RoleRoute>} />
      <Route path="/ordenes/:id/editar" element={<RoleRoute allowedRoles={orderRoles}><EditOrderPage /></RoleRoute>} />
    </Route>
    <Route path="*" element={<Navigate to="/dashboard" replace />} />
  </Routes>
}

export default function App() {
  return <AuthProvider><AppRoutes /></AuthProvider>
}
