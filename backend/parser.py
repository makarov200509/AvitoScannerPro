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
    _semaphore = threading.Semaphore(100)
    
    def __init__(self):
        self.driver = None
    
    def setup_driver(self):
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
        encoded_query = urllib.parse.quote(search_query)
        
        if city_code == 'all':
            base_url = "https://www.avito.ru"
            params = [f"q={encoded_query}", "s=104"]
        else:
            base_url = f"https://www.avito.ru/{city_code}"
            params = [f"q={encoded_query}", "s=104"]
        
        if page > 1:
            params.append(f"p={page}")
        
        if price_min and price_min > 0:
            params.append(f"pmin={price_min}")
        if price_max and price_max > 0:
            params.append(f"pmax={price_max}")
        
        return base_url + "?" + "&".join(params)

    def is_captcha_present(self):
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
        
        print(f"[QUEUE] Ожидание слота...")
        AvitoParser._semaphore.acquire()
        print(f"[QUEUE] Слот получен")
        
        try:
            self.setup_driver()
            all_results = []
            
            for page in range(1, pages + 1):
                if check_active_callback and not check_active_callback():
                    break
                
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
                            print(f"[PARSER] Найдено {len(items)} карточек")
                            break
                    except Exception as e:
                        continue
                
                if not items:
                    print(f"[PARSER] Карточки не найдены")
                    break
                
                time.sleep(2)
                page_results = self.parse_items(items, max_items - len(all_results))
                all_results.extend(page_results)
                
                if len(all_results) >= max_items:
                    all_results = all_results[:max_items]
                    break
            
            unique_ads = {}
            for ad in all_results:
                if ad['ad_id'] not in unique_ads:
                    unique_ads[ad['ad_id']] = ad
            
            final_results = list(unique_ads.values())
            print(f"[PARSER] Всего обработано {len(final_results)} объявлений")
            return final_results
            
        except Exception as e:
            print(f"[PARSER] Ошибка парсинга: {e}")
            return []
        finally:
            self.close()
            AvitoParser._semaphore.release()

    def get_price(self, item):
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
        
        try:
            price_elem = item.find_element(By.CSS_SELECTOR, '[data-marker="item-price"]')
            parent = price_elem.find_element(By.XPATH, '..')
            siblings = parent.find_elements(By.XPATH, './*')
            
            for sibling in siblings:
                text = sibling.text.strip()
                if text and 5 < len(text) < 80:
                    if ',' in text and ('мин' in text or 'метро' in text.lower()):
                        return text.split(',')[0].strip()
                    if any(hint in text.lower() for hint in ['метро', 'м.', 'район', 'ул.', 'пр-т']):
                        return text
        except:
            pass
        
        try:
            all_text = item.text.split('\n')
            for line in all_text:
                line = line.strip()
                if line and ',' in line and 'мин' in line:
                    if not any(skip in line for skip in ['₽', 'руб', 'Доставка', 'Рассрочка', 'Б/у']):
                        return line.split(',')[0].strip()
        except:
            pass
        
        try:
            location_elem = item.find_element(By.CSS_SELECTOR, '[data-marker="item-address"]')
            location_text = location_elem.text.strip()
            if location_text:
                return ' '.join(location_text.split())
        except:
            pass
        
        return "Местоположение не указано"

    def get_title(self, item):
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
                    
                    if location != "Местоположение не указано":
                        print(f"[DEBUG] Найден адрес: {location}")
                    
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
            
            return results
            
        except Exception as e:
            print(f"Ошибка parse_items: {e}")
            return []

    def close(self):
        if self.driver:
            try:
                self.driver.quit()
                print("[PARSER] Браузер закрыт")
            except:
                pass


def shutdown_parser_pool():
    print("[PARSER] shutdown_parser_pool вызван")