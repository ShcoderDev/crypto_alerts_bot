<template>
  <div id="app">
    <div class="container">
      <h1>🔔 Crypto Alerts</h1>
      <p class="subtitle">Настройте уведомления о ценах криптовалют</p>

      <div v-if="error" class="error">{{ error }}</div>
      <div v-if="success" class="success">{{ success }}</div>

      <AlertForm
        v-if="!editingAlert"
        :cryptocurrencies="cryptocurrencies"
        @submit="createAlert"
        @cancel="cancelEdit"
      />

      <AlertForm
        v-else
        :cryptocurrencies="cryptocurrencies"
        :alert="editingAlert"
        @submit="updateAlert"
        @cancel="cancelEdit"
      />

      <PriceChart :cryptocurrencies="cryptocurrencies" />

      <h2>Мои алерты</h2>
      <div v-if="loading" class="loading">Загрузка...</div>
      <div v-else-if="alerts.length === 0" class="empty-state">
        <div class="empty-state-icon">📭</div>
        <p>У вас пока нет активных алертов</p>
        <p style="font-size: 12px; margin-top: 8px;">Создайте первый алерт выше</p>
      </div>
      <div v-else class="alert-list">
        <AlertItem
          v-for="alert in alerts"
          :key="alert.id"
          :alert="alert"
          @edit="startEdit"
          @delete="deleteAlert"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import AlertForm from './components/AlertForm.vue'
import AlertItem from './components/AlertItem.vue'
import PriceChart from './components/PriceChart.vue'
import { getUserId, fetchCryptocurrencies, fetchAlerts, createAlert as apiCreateAlert, updateAlert as apiUpdateAlert, deleteAlert as apiDeleteAlert } from './api'
import type { Alert, AlertCreate } from './types'

const cryptocurrencies = ref<string[]>([])
const alerts = ref<Alert[]>([])
const loading = ref(true)
const error = ref('')
const success = ref('')
const editingAlert = ref<Alert | null>(null)
const userId = ref<number | null>(null)

onMounted(async () => {
  try {
    userId.value = await getUserId()
    await loadData()
  } catch (err: any) {
    error.value = 'Ошибка инициализации: ' + (err.message || 'Неизвестная ошибка')
  } finally {
    loading.value = false
  }
})

async function loadData() {
  try {
    const [cryptos, userAlerts] = await Promise.all([
      fetchCryptocurrencies(),
      userId.value ? fetchAlerts(userId.value) : Promise.resolve([])
    ])
    cryptocurrencies.value = cryptos
    alerts.value = userAlerts
  } catch (err: any) {
    error.value = 'Ошибка загрузки данных: ' + (err.message || 'Неизвестная ошибка')
  }
}

async function createAlert(alertData: AlertCreate) {
  if (!userId.value) {
    error.value = 'Пользователь не определен'
    return
  }

  try {
    error.value = ''
    const newAlert = await apiCreateAlert(userId.value, alertData)
    alerts.value.unshift(newAlert)
    success.value = 'Алерт успешно создан!'
    setTimeout(() => { success.value = '' }, 3000)
  } catch (err: any) {
    error.value = 'Ошибка создания алерта: ' + (err.message || 'Неизвестная ошибка')
  }
}

async function updateAlert(alertData: AlertCreate) {
  if (!userId.value || !editingAlert.value) return

  try {
    error.value = ''
    const updated = await apiUpdateAlert(editingAlert.value.id, userId.value, alertData)
    const index = alerts.value.findIndex(a => a.id === editingAlert.value!.id)
    if (index !== -1) {
      alerts.value[index] = updated
    }
    editingAlert.value = null
    success.value = 'Алерт успешно обновлен!'
    setTimeout(() => { success.value = '' }, 3000)
  } catch (err: any) {
    error.value = 'Ошибка обновления алерта: ' + (err.message || 'Неизвестная ошибка')
  }
}

async function deleteAlert(alertId: number) {
  if (!userId.value) return

  if (!confirm('Вы уверены, что хотите удалить этот алерт?')) {
    return
  }

  try {
    error.value = ''
    await apiDeleteAlert(alertId, userId.value)
    alerts.value = alerts.value.filter(a => a.id !== alertId)
    success.value = 'Алерт успешно удален!'
    setTimeout(() => { success.value = '' }, 3000)
  } catch (err: any) {
    error.value = 'Ошибка удаления алерта: ' + (err.message || 'Неизвестная ошибка')
  }
}

function startEdit(alert: Alert) {
  editingAlert.value = alert
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

function cancelEdit() {
  editingAlert.value = null
}
</script>

