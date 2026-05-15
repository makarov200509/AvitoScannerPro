import time
import random
import urllib.parse
import threading
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException

from config import PARSER_SETTINGS


class AvitoParser:
    _semaphore = threading.Semaphore(100)  # Максимум 100 браузеров одновременно
    
    def __init__(self):
        self.driver = None
    
    def setup_driver(self):
        """Настройка Chrome драйвера"""
        chrome_options = Options()
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        
        resolutions = ["1920,1080", "1366,768", "1536,864"]
        chrome_options.add_argument(f"--window-size={random.choice(resolutions)}")
        
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        ]
        chrome_options.add_argument(f"--user-agent={random.choice(user_agents)}")
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        except Exception as e:
            print(f"Ошибка драйвера: {e}")
            raise

    def build_avito_url(self, search_query, city_code, price_min=None, price_max=None, page=1):
        """Построение URL для поиска на Avito с поддержкой пагинации через p="""
        encoded_query = urllib.parse.quote(search_query)
        
        if city_code == 'all':
            base_url = "https://www.avito.ru"
            params = [f"q={encoded_query}", "s=104"]
        else:
            base_url = f"https://www.avito.ru/{city_code}"
            params = [f"q={encoded_query}", "s=104"]
        
        # Добавляем номер страницы для пагинации
        if page > 1:
            params.append(f"p={page}")
        
        if price_min and price_min > 0:
            params.append(f"pmin={price_min}")
        if price_max and price_max > 0:
            params.append(f"pmax={price_max}")
        
        return base_url + "?" + "&".join(params)

    def is_captcha_present(self):
        """Проверка наличия капчи или защиты"""
        indicators = [
            '//*[contains(text(), "Подтвердите, что вы не робот")]',
            '//*[contains(text(), "Обновите страницу")]',
            '//*[contains(text(), "Произошла ошибка")]',
            '//iframe[contains(@src, "captcha")]',
        ]
        
        for xpath in indicators:
            try:
                if self.driver.find_element(By.XPATH, xpath):
                    return True
            except:
                continue
        return False

    def handle_captcha(self, user_id=None):
        """Обработка капчи и защиты Avito"""
        print("Обнаружена защита Avito!")
        
        try:
            self.driver.delete_all_cookies()
            self.driver.execute_script("window.localStorage.clear();")
            self.driver.execute_script("window.sessionStorage.clear();")
            
            time.sleep(5)
            self.driver.refresh()
            time.sleep(5)
            
            if self.is_captcha_present():
                print("Капча все еще присутствует, пробуем еще раз...")
                time.sleep(10)
                self.driver.refresh()
                time.sleep(5)
            
            return not self.is_captcha_present()
            
        except Exception as e:
            print(f"Ошибка обработки капчи: {e}")
            return False

    def parse_avito(self, search_query, city_code, price_min=None, price_max=None, 
                    max_items=50, user_id=None, pages=1, check_active_callback=None):
        """Основной метод парсинга Avito с пагинацией через URL"""
        
        # Ждём своей очереди
        print(f"[QUEUE] Ожидание слота... (активно: {100 - AvitoParser._semaphore._value})")
        AvitoParser._semaphore.acquire()
        print(f"[QUEUE] Слот получен, запускаю браузер")
        
        try:
            self.setup_driver()
            all_results = []
            
            for page in range(1, pages + 1):
                if check_active_callback and not check_active_callback():
                    break
                
                # Строим URL с номером страницы
                url = self.build_avito_url(search_query, city_code, price_min, price_max, page)
                print(f"[PARSER] Парсим страницу {page}: {url}")
                
                self.driver.get(url)
                time.sleep(random.uniform(PARSER_SETTINGS['min_sleep'], PARSER_SETTINGS['max_sleep']))
                
                if self.is_captcha_present():
                    print("Обнаружена защита Avito")
                    if not self.handle_captcha(user_id):
                        return []
                
                wait = WebDriverWait(self.driver, PARSER_SETTINGS['default_timeout'])
                
                selectors_to_try = [
                    '[data-marker="item"]',
                    '.iva-item-root',
                    '.items-items-kAJAg'
                ]
                
                items = []
                for selector in selectors_to_try:
                    try:
                        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                        items = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        if items:
                            print(f"[PARSER] Страница {page}: найдено {len(items)} карточек")
                            break
                    except Exception as e:
                        print(f"[PARSER] Селектор {selector} не сработал: {e}")
                        continue
                
                if not items:
                    print(f"[PARSER] Страница {page}: карточки не найдены, завершаем")
                    break
                
                time.sleep(2)
                page_results = self.parse_items(items, max_items - len(all_results))
                all_results.extend(page_results)
                
                print(f"[PARSER] Страница {page}: собрано {len(page_results)} объявлений, всего: {len(all_results)}")
                
                if len(all_results) >= max_items:
                    all_results = all_results[:max_items]
                    break
            
            # Дедупликация
            unique_ads = {}
            for ad in all_results:
                if ad['ad_id'] not in unique_ads:
                    unique_ads[ad['ad_id']] = ad
            
            final_results = list(unique_ads.values())
            print(f"[PARSER] Всего обработано {len(final_results)} уникальных объявлений с {pages} страниц")
            return final_results
            
        except Exception as e:
            print(f"[PARSER] Ошибка парсинга: {e}")
            return []
        finally:
            self.close()
            AvitoParser._semaphore.release()
            print(f"[QUEUE] Слот освобождён, активно: {100 - AvitoParser._semaphore._value}")

    def get_price(self, item):
        """Извлечение цены"""
        price_selectors = [
            '[data-marker="item-price"]',
            '.price-price-ZMrtW', 
            '.iva-item-priceStep-TVego',
        ]
        
        for selector in price_selectors:
            try:
                price_elem = item.find_element(By.CSS_SELECTOR, selector)
                price_text = price_elem.text.strip()
                if price_text and any(char.isdigit() for char in price_text):
                    return price_text
            except NoSuchElementException:
                continue
        return "Цена не указана"

    def get_location(self, item):
        """Извлечение местоположения"""
        location_selectors = [
            '[data-marker="item-address"]',
            '.iva-item-location-3yQ4y',
            '.geo-georeferences-SEtee',
            '.geo-root-zPwRk',
            '[class*="geo-address"]',
            '[class*="location"]',
            '.style-item-address-3JoB0'
        ]
        
        for selector in location_selectors:
            try:
                location_elem = item.find_element(By.CSS_SELECTOR, selector)
                location_text = location_elem.text.strip()
                if location_text and len(location_text) > 2:
                    location_text = ' '.join(location_text.split())
                    return location_text
            except NoSuchElementException:
                continue
        
        try:
            address_indicators = ['р-н', 'ул.', 'пр-т', 'мкр', 'д.', 'кв.', 'метро', 'Москва', 'Санкт-Петербург']
            all_elements = item.find_elements(By.XPATH, ".//*")
            for elem in all_elements:
                text = elem.text.strip()
                if any(indicator in text for indicator in address_indicators) and len(text) < 100:
                    return text
        except:
            pass
        
        return "Местоположение не указано"

    def get_title(self, item):
        """Извлечение заголовка"""
        title_selectors = [
            '[itemprop="name"]',
            '[data-marker="item-title"]',
            'h3'
        ]
        
        for selector in title_selectors:
            try:
                title_elem = item.find_element(By.CSS_SELECTOR, selector)
                title = title_elem.text.strip()
                if title:
                    return title
            except NoSuchElementException:
                continue
        return "Без названия"

    def get_date(self, item):
        """Извлечение даты публикации"""
        date_selectors = [
            '[data-marker="item-date"]',
            '.iva-item-date-2vwf_'
        ]
        
        for selector in date_selectors:
            try:
                date_elem = item.find_element(By.CSS_SELECTOR, selector)
                date_text = date_elem.text.strip()
                if date_text:
                    return date_text
            except NoSuchElementException:
                continue
        return "Сегодня"

    def get_link(self, item):
        """Извлечение ссылки на объявление"""
        try:
            link_selectors = [
                'a[href*="/"]',
                '[data-marker="item-title"]'
            ]
            
            for selector in link_selectors:
                try:
                    link_elem = item.find_element(By.CSS_SELECTOR, selector)
                    link = link_elem.get_attribute('href')
                    if link and not link.startswith('http'):
                        link = f"https://www.avito.ru{link}"
                    if link:
                        return link
                except NoSuchElementException:
                    continue
        except:
            pass
        return ""

    def parse_items(self, items, max_items=50):
        """Парсинг списка карточек товаров"""
        try:
            items = items[:max_items]
            results = []
            
            for item in items:
                try:
                    title = self.get_title(item)
                    price = self.get_price(item)
                    link = self.get_link(item)
                    date = self.get_date(item)
                    location = self.get_location(item)
                    
                    ad_id = link.split('/')[-1].split('?')[0] if link else str(random.randint(100000, 999999))
                    
                    results.append({
                        'title': title,
                        'price': price,
                        'link': link,
                        'date': date,
                        'location': location,
                        'ad_id': ad_id
                    })
                    
                except Exception as e:
                    continue
            
            print(f"Обработано {len(results)} объявлений")
            return results
            
        except Exception as e:
            print(f"Ошибка парсинга карточек: {e}")
            return []

    def close(self):
        """Закрытие драйвера"""
        if self.driver:
            try:
                self.driver.quit()
                print("[PARSER] Браузер закрыт")
            except:
                pass


def shutdown_parser_pool():
    """Заглушка для совместимости с web_app.py"""
    print("[PARSER] shutdown_parser_pool вызван (ничего не делаем)")