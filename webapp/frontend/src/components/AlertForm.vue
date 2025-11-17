<template>
  <form @submit.prevent="handleSubmit" class="alert-form">
    <div class="form-group">
      <label>Криптовалюта</label>
      <select v-model="form.cryptocurrency" required>
        <option value="">Выберите криптовалюту</option>
        <option v-for="crypto in cryptocurrencies" :key="crypto" :value="crypto">
          {{ crypto }}
        </option>
      </select>
    </div>

    <div class="form-group">
      <label>Целевая цена (USDT)</label>
      <input
        type="number"
        v-model.number="form.target_price"
        step="0.01"
        min="0.01"
        required
        placeholder="0.00"
      />
    </div>

    <div class="form-group">
      <label>Уведомить, когда цена будет</label>
      <div class="radio-group">
        <label
          class="radio-option"
          :class="{ active: form.is_above }"
          @click="form.is_above = true"
        >
          <input type="radio" v-model="form.is_above" :value="true" />
          Выше
        </label>
        <label
          class="radio-option"
          :class="{ active: !form.is_above }"
          @click="form.is_above = false"
        >
          <input type="radio" v-model="form.is_above" :value="false" />
          Ниже
        </label>
      </div>
    </div>

    <button type="submit" class="btn btn-primary">
      {{ alert ? 'Обновить алерт' : 'Создать алерт' }}
    </button>
    <button
      v-if="alert"
      type="button"
      class="btn btn-secondary"
      @click="$emit('cancel')"
    >
      Отмена
    </button>
  </form>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import type { Alert, AlertCreate } from '../types'

const props = defineProps<{
  cryptocurrencies: string[]
  alert?: Alert | null
}>()

const emit = defineEmits<{
  submit: [data: AlertCreate]
  cancel: []
}>()

const form = ref<AlertCreate>({
  cryptocurrency: '',
  target_price: 0,
  is_above: true
})

onMounted(() => {
  if (props.alert) {
    form.value = {
      cryptocurrency: props.alert.cryptocurrency,
      target_price: props.alert.target_price,
      is_above: props.alert.is_above
    }
  }
})

function handleSubmit() {
  emit('submit', { ...form.value })
  if (!props.alert) {
    form.value = {
      cryptocurrency: '',
      target_price: 0,
      is_above: true
    }
  }
}
</script>

