export function useFormatters() {
  const formatNumber = (num) => {
    if (!num && num !== 0) return '0'
    if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M'
    if (num >= 1000) return (num / 1000).toFixed(0) + 'K'
    return num.toString()
  }
  
  const formatPrice = (price) => {
    if (!price && price !== 0) return '0 ₽'
    return new Intl.NumberFormat('ru-RU').format(price) + ' ₽'
  }
  
  const formatPriceNum = (price) => {
    if (!price && price !== 0) return '0'
    return new Intl.NumberFormat('ru-RU').format(price)
  }
  
  const formatDate = (dateStr) => {
    if (!dateStr) return ''
    try {
      const date = new Date(dateStr)
      if (isNaN(date.getTime())) return dateStr
      return date.toLocaleString('ru-RU', {
        day: '2-digit',
        month: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
      })
    } catch {
      return dateStr
    }
  }
  
  const formatDateWithYear = (dateStr) => {
    if (!dateStr) return ''
    try {
      const date = new Date(dateStr)
      if (isNaN(date.getTime())) return dateStr
      return date.toLocaleString('ru-RU', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      })
    } catch {
      return dateStr
    }
  }
  
  const formatTime = (timestamp) => {
    if (!timestamp) return '—'
    try {
      const date = new Date(timestamp)
      if (isNaN(date.getTime())) return '—'
      return date.toLocaleTimeString('ru-RU', {
        hour: '2-digit',
        minute: '2-digit'
      })
    } catch {
      return '—'
    }
  }
  
  const formatTimeLeft = (endTime) => {
    if (!endTime) return '—'
    try {
      const end = new Date(endTime)
      if (isNaN(end.getTime())) return '—'
      const left = Math.max(0, Math.floor((end - Date.now()) / 60000))
      if (left <= 0) return 'Завершается'
      if (left < 60) return left + ' мин'
      const hours = Math.floor(left / 60)
      const minutes = left % 60
      return minutes > 0 ? hours + ' ч ' + minutes + ' мин' : hours + ' ч'
    } catch {
      return '—'
    }
  }
  
  const getProcessType = (type) => {
    const types = {
      search: 'Поиск',
      monitoring: 'Мониторинг',
      analysis: 'Анализ'
    }
    return types[type] || type
  }
  
  return {
    formatNumber,
    formatPrice,
    formatPriceNum,
    formatDate,
    formatDateWithYear,
    formatTime,
    formatTimeLeft,
    getProcessType
  }
}