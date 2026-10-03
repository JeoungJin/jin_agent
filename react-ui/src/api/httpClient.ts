import axios from 'axios'

// 401 수신 시 App이 로그인 화면으로 전환하도록 등록하는 핸들러
let onUnauthorized: () => void = () => {}
export const setUnauthorizedHandler = (fn: () => void) => {
  onUnauthorized = fn
}

export const httpClient = axios.create({ withCredentials: true })

httpClient.interceptors.response.use(
  (res) => res,
  (error) => {
    if (error.response?.status === 401) onUnauthorized()
    return Promise.reject(error)
  },
)
