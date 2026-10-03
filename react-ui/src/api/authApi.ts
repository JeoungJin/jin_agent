import { httpClient } from './httpClient'

export interface LoginResponse {
  id: number
  email: string
}

export const login = (email: string) =>
  httpClient.post<LoginResponse>('/api/auth/login', { email }).then((r) => r.data)

export const logout = () => httpClient.post('/api/auth/logout')

export const fetchMe = () =>
  httpClient.get('/api/ai/me').then((r) => r.data)
