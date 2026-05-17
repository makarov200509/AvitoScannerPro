let csrfToken = null
let isInterceptorInstalled = false

export const fetchCsrfToken = async () => {
  try {
    const response = await fetch('/api/csrf-token')
    const data = await response.json()
    csrfToken = data.csrf_token
    sessionStorage.setItem('csrf_token', csrfToken)
    return csrfToken
  } catch (error) {
    console.error('Failed to fetch CSRF token:', error)
    return null
  }
}

export const getCsrfToken = () => {
  if (!csrfToken) {
    csrfToken = sessionStorage.getItem('csrf_token')
  }
  return csrfToken
}

export const setupCsrfInterceptor = () => {
  if (isInterceptorInstalled) {
    return
  }
  
  const originalFetch = window.fetch
  
  window.fetch = async function(url, options = {}) {
    const method = options.method || 'GET'
    
    if (method !== 'GET' && method !== 'HEAD' && method !== 'OPTIONS') {
      let token = getCsrfToken()
      
      if (!token) {
        token = await fetchCsrfToken()
      }
      
      if (token) {
        options.headers = {
          ...options.headers,
          'X-CSRF-Token': token
        }
      }
    }
    
    return originalFetch.call(this, url, options)
  }
  
  isInterceptorInstalled = true
}