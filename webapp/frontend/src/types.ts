export interface Alert {
  id: number
  user_id: number
  cryptocurrency: string
  target_price: number
  is_above: boolean
  created_at: string
  is_active: boolean
}

export interface AlertCreate {
  cryptocurrency: string
  target_price: number
  is_above: boolean
}

export interface AlertUpdate {
  cryptocurrency?: string
  target_price?: number
  is_above?: boolean
}

