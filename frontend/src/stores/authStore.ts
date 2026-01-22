import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface User {
  id: number
  username: string
  role: 'admin' | 'teacher' | 'student'
  real_name?: string
}

interface AuthState {
  token: string | null
  user: User | null
  setAuth: (token: string, user: User) => void
  logout: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      user: null,
      setAuth: (token, user) => {
        localStorage.setItem('token', token)
        set({ token, user })
      },
      logout: () => {
        localStorage.removeItem('token')
        set({ token: null, user: null })
      },
    }),
    {
      name: 'auth-storage',
      onRehydrateStorage: () => (state) => {
        // 当从持久化存储恢复时，同步token到localStorage
        if (state?.token) {
          localStorage.setItem('token', state.token)
        }
      },
    }
  )
)
