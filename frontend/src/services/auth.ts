const ACCESS_TOKEN_KEY = 'access_token'
const REFRESH_TOKEN_KEY = 'refresh_token'
const USER_KEY = 'user'

export interface User {
  user_id: string
  username: string
  phone?: string
  created_at: string
}

const LOCAL_USER: User = {
  user_id: 'local_user',
  username: '本地用户',
  created_at: new Date().toISOString()
}

const LOCAL_TOKEN = 'local_mock_token_for_single_user_mode'

export function getToken(): string | null {
  return localStorage.getItem(ACCESS_TOKEN_KEY)
}

export function getRefreshToken(): string | null {
  return localStorage.getItem(REFRESH_TOKEN_KEY)
}

export function setTokens(accessToken: string, refreshToken: string) {
  localStorage.setItem(ACCESS_TOKEN_KEY, accessToken)
  localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken)
}

export function clearTokens() {
  localStorage.removeItem(ACCESS_TOKEN_KEY)
  localStorage.removeItem(REFRESH_TOKEN_KEY)
  localStorage.removeItem(USER_KEY)
}

export function getUser(): User | null {
  const userStr = localStorage.getItem(USER_KEY)
  if (userStr) {
    try {
      return JSON.parse(userStr)
    } catch {
      return null
    }
  }
  return null
}

export function setUser(user: User) {
  localStorage.setItem(USER_KEY, JSON.stringify(user))
}

export function isLoggedIn(): boolean {
  return !!getToken()
}

export async function ensureLocalUser(): Promise<void> {
  if (!isLoggedIn()) {
    setTokens(LOCAL_TOKEN, LOCAL_TOKEN)
    setUser(LOCAL_USER)
  }
}
