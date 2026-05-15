import { useToastStore } from '@/stores/toast'

export function useApi() {
  const toastStore = useToastStore()
  
  const fetchWithError = async (url, options = {}) => {
    try {
      const response = await fetch(url, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          ...options.headers
        }
      })
      
      const data = await response.json()
      
      if (!response.ok) {
        throw new Error(data.error || 'Произошла ошибка')
      }
      
      return { success: true, data }
    } catch (error) {
      toastStore.addToast(error.message, 'error')
      return { success: false, error: error.message }
    }
  }
  
  const post = async (url, body) => {
    return fetchWithError(url, {
      method: 'POST',
      body: JSON.stringify(body)
    })
  }
  
  const get = async (url) => {
    return fetchWithError(url, {
      method: 'GET'
    })
  }
  
  const del = async (url) => {
    return fetchWithError(url, {
      method: 'DELETE'
    })
  }
  
  return {
    fetchWithError,
    post,
    get,
    del
  }
}