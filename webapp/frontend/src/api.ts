import type { Alert, AlertCreate, AlertUpdate } from './types'

const API_BASE = '/api'

// Получение user_id из Telegram WebApp
export async function getUserId(): Promise<number> {
  if (window.Telegram?.WebApp?.initDataUnsafe?.user?.id) {
    return window.Telegram.WebApp.initDataUnsafe.user.id
  }
  throw new Error('Не удалось получить ID пользователя из Telegram')
}

// Получение списка криптовалют
export async function fetchCryptocurrencies(): Promise<string[]> {
  const response = await fetch(`${API_BASE}/cryptocurrencies`)
  if (!response.ok) {
    throw new Error('Ошибка загрузки криптовалют')
  }
  const data = await response.json()
  return data.cryptocurrencies
}

// Получение алертов пользователя
export async function fetchAlerts(userId: number): Promise<Alert[]> {
  const response = await fetch(`${API_BASE}/alerts?user_id=${userId}`)
  if (!response.ok) {
    throw new Error('Ошибка загрузки алертов')
  }
  return response.json()
}

// Создание алерта
export async function createAlert(userId: number, alertData: AlertCreate): Promise<Alert> {
  const response = await fetch(`${API_BASE}/alerts?user_id=${userId}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(alertData)
  })
  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || 'Ошибка создания алерта')
  }
  return response.json()
}

// Обновление алерта
export async function updateAlert(alertId: number, userId: number, alertData: AlertUpdate): Promise<Alert> {
  const response = await fetch(`${API_BASE}/alerts/${alertId}?user_id=${userId}`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(alertData)
  })
  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || 'Ошибка обновления алерта')
  }
  return response.json()
}

// Удаление алерта
export async function deleteAlert(alertId: number, userId: number): Promise<void> {
  const response = await fetch(`${API_BASE}/alerts/${alertId}?user_id=${userId}`, {
    method: 'DELETE'
  })
  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || 'Ошибка удаления алерта')
  }
}

// Расширение Window для TypeScript
declare global {
  interface Window {
    Telegram?: {
      WebApp?: {
        initDataUnsafe?: {
          user?: {
            id: number
            username?: string
            first_name?: string
          }
        }
        ready?: () => void
        expand?: () => void
      }
    }
  }
}

