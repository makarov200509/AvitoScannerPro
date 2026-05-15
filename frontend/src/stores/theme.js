import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useThemeStore = defineStore('theme', () => {
  const currentTheme = ref('dark')
  
  const setTheme = (theme) => {
    currentTheme.value = theme
    document.body.classList.remove('dark-theme', 'light-theme')
    document.body.classList.add(theme + '-theme')
    localStorage.setItem('theme', theme)
  }
  
  const initTheme = () => {
    const saved = localStorage.getItem('theme')
    if (saved && (saved === 'dark' || saved === 'light')) {
      setTheme(saved)
    } else {
      setTheme('dark')
    }
  }
  
  const cycleTheme = () => {
    const newTheme = currentTheme.value === 'dark' ? 'light' : 'dark'
    setTheme(newTheme)
  }
  
  const themeButtonText = () => {
    return currentTheme.value === 'dark' ? 'Светлая' : 'Тёмная'
  }
  
  return {
    currentTheme,
    setTheme,
    initTheme,
    cycleTheme,
    themeButtonText
  }
})