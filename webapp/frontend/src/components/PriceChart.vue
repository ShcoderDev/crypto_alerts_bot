<template>
  <div class="chart-container">
    <div class="chart-header">
      <h2>📈 График цены</h2>
      <select v-model="selectedCrypto" @change="onCryptoChange" class="crypto-select">
        <option value="">Выберите валюту</option>
        <option v-for="crypto in cryptocurrencies" :key="crypto" :value="crypto">
          {{ crypto }}
        </option>
      </select>
    </div>
    <div v-if="selectedCrypto" class="chart-wrapper">
      <div ref="chartContainer" class="chart"></div>
      <div class="chart-info">
        <div class="price-info">
          <span class="label">Текущая цена:</span>
          <span class="price" :class="{ up: priceChange > 0, down: priceChange < 0 }">
            ${{ currentPrice.toLocaleString('ru-RU', { minimumFractionDigits: 2, maximumFractionDigits: 8 }) }}
          </span>
          <span v-if="priceChange !== 0" class="change" :class="{ up: priceChange > 0, down: priceChange < 0 }">
            {{ priceChange > 0 ? '+' : '' }}{{ priceChange.toFixed(2) }}%
          </span>
        </div>
      </div>
    </div>
    <div v-else class="empty-chart">
      <div class="empty-state-icon">📊</div>
      <p>Выберите криптовалюту для просмотра графика</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { createChart, IChartApi, ISeriesApi, CandlestickData, Time } from 'lightweight-charts'

const props = defineProps<{
  cryptocurrencies: string[]
}>()

const chartContainer = ref<HTMLDivElement | null>(null)
const selectedCrypto = ref<string>('')
const currentPrice = ref<number>(0)
const priceChange = ref<number>(0)
const previousPrice = ref<number>(0)

let chart: IChartApi | null = null
let candlestickSeries: ISeriesApi<'Candlestick'> | null = null
let ws: WebSocket | null = null
let candles: Map<number, CandlestickData> = new Map()
let resizeObserver: ResizeObserver | null = null

function initChart() {
  if (!chartContainer.value || chart) return

  try {
    chart = createChart(chartContainer.value, {
      width: chartContainer.value.clientWidth,
      height: 400,
      layout: {
        background: { color: '#ffffff' },
        textColor: '#333',
      },
      grid: {
        vertLines: { color: '#f0f0f0' },
        horzLines: { color: '#f0f0f0' },
      },
      timeScale: {
        timeVisible: true,
        secondsVisible: false,
      },
    })

    candlestickSeries = chart.addCandlestickSeries({
      upColor: '#26a69a',
      downColor: '#ef5350',
      borderVisible: false,
      wickUpColor: '#26a69a',
      wickDownColor: '#ef5350',
    })

    // Обработка изменения размера
    resizeObserver = new ResizeObserver(() => {
      if (chart && chartContainer.value) {
        chart.applyOptions({ width: chartContainer.value.clientWidth })
      }
    })
    if (chartContainer.value) {
      resizeObserver.observe(chartContainer.value)
    }
  } catch (error) {
    console.error('Ошибка инициализации графика:', error)
  }
}

onMounted(() => {
  // График будет создан при выборе криптовалюты
})

onUnmounted(() => {
  if (ws) {
    ws.close()
    ws = null
  }
  if (resizeObserver) {
    resizeObserver.disconnect()
    resizeObserver = null
  }
  if (chart) {
    chart.remove()
    chart = null
  }
  candlestickSeries = null
})

function onCryptoChange() {
  if (ws) {
    ws.close()
    ws = null
  }
  
  // Удаляем старый график
  if (chart) {
    chart.remove()
    chart = null
    candlestickSeries = null
  }
  if (resizeObserver) {
    resizeObserver.disconnect()
    resizeObserver = null
  }
  
  candles.clear()
  currentPrice.value = 0
  priceChange.value = 0
  previousPrice.value = 0

  if (selectedCrypto.value) {
    // Ждем следующего тика, чтобы DOM обновился
    setTimeout(() => {
      initChart()
      if (candlestickSeries) {
        loadHistoricalData()
        connectWebSocket()
      }
    }, 100)
  }
}

async function loadHistoricalData() {
  if (!selectedCrypto.value || !candlestickSeries) {
    console.warn('Не готов к загрузке данных:', { selectedCrypto: selectedCrypto.value, candlestickSeries: !!candlestickSeries })
    return
  }

  try {
    const symbol = `${selectedCrypto.value.toUpperCase()}USDT`
    console.log('Загрузка исторических данных для', symbol)
    
    // Получаем исторические данные свечей (1 минута) за последний час через наш бэкенд
    const response = await fetch(
      `/api/candles?symbol=${symbol}&interval=1m&limit=60`
    )
    if (!response.ok) {
      const errorText = await response.text()
      throw new Error(`Ошибка загрузки данных: ${response.status} ${errorText}`)
    }
    const data = await response.json()

    if (!data.candles || !Array.isArray(data.candles)) {
      throw new Error('Некорректный формат данных')
    }

    const candleData: CandlestickData[] = data.candles.map((candle: any) => ({
      time: candle.time as Time,
      open: candle.open,
      high: candle.high,
      low: candle.low,
      close: candle.close,
    }))

    console.log('Загружено свечей:', candleData.length)

    if (candlestickSeries && candleData.length > 0) {
      candlestickSeries.setData(candleData)
      
      // Сохраняем свечи в Map
      candleData.forEach(candle => {
        candles.set(candle.time as number, candle)
      })

      // Устанавливаем текущую цену
      const lastCandle = candleData[candleData.length - 1]
      currentPrice.value = lastCandle.close
      previousPrice.value = lastCandle.close
      priceChange.value = 0
      
      console.log('Текущая цена установлена:', currentPrice.value)
    }
  } catch (error) {
    console.error('Ошибка загрузки исторических данных:', error)
    currentPrice.value = 0
  }
}

function connectWebSocket() {
  if (!selectedCrypto.value) return

  const symbol = `${selectedCrypto.value.toLowerCase()}usdt`
  // Используем прокси через наш сервер вместо прямого подключения к Binance
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const wsUrl = `${protocol}//${window.location.host}/ws/binance/${symbol}`

  try {
    ws = new WebSocket(wsUrl)

    ws.onopen = () => {
      console.log('WebSocket подключен для', symbol)
    }

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        const price = parseFloat(data.c)
        
        if (isNaN(price) || price <= 0) {
          console.warn('Некорректная цена:', data.c)
          return
        }

        const timestamp = Math.floor(Date.now() / 1000)
        const currentMinute = Math.floor(timestamp / 60) * 60

        // Обновляем текущую цену
        if (currentPrice.value > 0) {
          previousPrice.value = currentPrice.value
          priceChange.value = ((price - previousPrice.value) / previousPrice.value) * 100
        } else {
          priceChange.value = 0
        }
        currentPrice.value = price

        // Обновляем последнюю свечу или создаем новую
        const existingCandle = candles.get(currentMinute)

        if (existingCandle && candlestickSeries) {
          // Обновляем существующую свечу
          const updatedCandle: CandlestickData = {
            ...existingCandle,
            close: price,
            high: Math.max(existingCandle.high, price),
            low: Math.min(existingCandle.low, price),
          }
          candles.set(currentMinute, updatedCandle)
          candlestickSeries.update(updatedCandle)
        } else if (candlestickSeries) {
          // Создаем новую свечу
          const newCandle: CandlestickData = {
            time: currentMinute as Time,
            open: price,
            high: price,
            low: price,
            close: price,
          }
          candles.set(currentMinute, newCandle)
          candlestickSeries.update(newCandle)
        }
      } catch (error) {
        console.error('Ошибка обработки WebSocket данных:', error)
      }
    }

    ws.onerror = (error) => {
      console.error('WebSocket ошибка:', error)
    }

    ws.onclose = () => {
      console.log('WebSocket закрыт, переподключение...')
      // Переподключение через 3 секунды
      setTimeout(() => {
        if (selectedCrypto.value && !ws) {
          connectWebSocket()
        }
      }, 3000)
    }
  } catch (error) {
    console.error('Ошибка создания WebSocket:', error)
  }
}
</script>

<style scoped>
.chart-container {
  background: white;
  border-radius: 20px;
  padding: 24px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
  margin-bottom: 20px;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  flex-wrap: wrap;
  gap: 12px;
}

.chart-header h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: #333;
}

.crypto-select {
  padding: 8px 16px;
  border: 2px solid #e0e0e0;
  border-radius: 12px;
  font-size: 14px;
  background: white;
  cursor: pointer;
  transition: all 0.3s ease;
}

.crypto-select:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.chart-wrapper {
  margin-top: 16px;
}

.chart {
  width: 100%;
  height: 400px;
  border-radius: 12px;
  overflow: hidden;
}

.chart-info {
  margin-top: 16px;
  padding: 12px;
  background: #f8f9fa;
  border-radius: 12px;
}

.price-info {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.label {
  font-size: 14px;
  color: #666;
  font-weight: 500;
}

.price {
  font-size: 20px;
  font-weight: 700;
  color: #333;
}

.price.up {
  color: #26a69a;
}

.price.down {
  color: #ef5350;
}

.change {
  font-size: 14px;
  font-weight: 600;
  padding: 4px 8px;
  border-radius: 6px;
}

.change.up {
  color: #26a69a;
  background: #e8f5f3;
}

.change.down {
  color: #ef5350;
  background: #fdeaea;
}

.empty-chart {
  text-align: center;
  padding: 60px 20px;
  color: #999;
}

.empty-state-icon {
  font-size: 64px;
  margin-bottom: 16px;
}

@media (max-width: 600px) {
  .chart-header {
    flex-direction: column;
    align-items: stretch;
  }

  .crypto-select {
    width: 100%;
  }

  .chart {
    height: 300px;
  }
}
</style>

