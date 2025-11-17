<template>
  <div class="alert-item">
    <div class="alert-header">
      <div class="alert-crypto">{{ alert.cryptocurrency }}</div>
      <div class="alert-price">${{ formatPrice(alert.target_price) }}</div>
    </div>
    <div
      class="alert-direction"
      :class="alert.is_above ? 'above' : 'below'"
    >
      {{ alert.is_above ? '↑ Выше' : '↓ Ниже' }}
    </div>
    <div class="alert-actions">
      <button class="btn btn-secondary" @click="$emit('edit', alert)">
        Редактировать
      </button>
      <button class="btn btn-danger" @click="$emit('delete', alert.id)">
        Удалить
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Alert } from '../types'

defineProps<{
  alert: Alert
}>()

defineEmits<{
  edit: [alert: Alert]
  delete: [id: number]
}>()

function formatPrice(price: number): string {
  return new Intl.NumberFormat('ru-RU', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 8
  }).format(price)
}
</script>

