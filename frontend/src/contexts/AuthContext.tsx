import { createContext, useContext, useEffect, useState } from 'react'
import { api, clearToken, getToken, setToken } from '../services/api'
import type { User } from '../types/api'
type AuthState = { token: string | null; user: User | null; loading: boolean; login: (email: string, password: string) => Promise<void>; logout: () => void }
const AuthContext = createContext<AuthState | undefined>(undefined)
export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [token, setTokenState] = useState(getToken()); const [user, setUser] = useState<User | null>(null); const [loading, setLoading] = useState(true)
  // La restauración se hace una vez por token almacenado.
  useEffect(() => { if (!token) { queueMicrotask(() => setLoading(false)); return } api.me().then(setUser).catch(() => { clearToken(); setTokenState(null) }).finally(() => setLoading(false)) }, [token])
  const login = async (email: string, password: string) => { const result = await api.login(email, password); setToken(result.access_token); setTokenState(result.access_token); setUser(await api.me()) }
  const logout = () => { clearToken(); setTokenState(null); setUser(null) }
  return <AuthContext.Provider value={{ token, user, loading, login, logout }}>{children}</AuthContext.Provider>
}
export function useAuth() { const value = useContext(AuthContext); if (!value) throw new Error('AuthContext no disponible'); return value }
