import re
from config import CITIES

def calculate_price_statistics(ads):
    prices = []
    
    for ad in ads:
        price_text = ad['price']
        if price_text and price_text != "Цена не указана":
            price_clean = re.sub(r'[^\d]', '', price_text)
            if price_clean:
                try:
                    price_value = int(price_clean)
                    if price_value > 0:
                        prices.append(price_value)
                except ValueError:
                    continue
    
    if not prices:
        return None
    
    prices_sorted = sorted(prices)
    n = len(prices_sorted)
    
    if n % 2 == 1:
        median = prices_sorted[n // 2]
    else:
        median = (prices_sorted[n // 2 - 1] + prices_sorted[n // 2]) // 2
    
    mean = sum(prices_sorted) // n
    min_price = prices_sorted[0]
    max_price = prices_sorted[-1]
    
    return {
        'count': n,
        'median': median,
        'mean': mean,
        'min': min_price,
        'max': max_price
    }

def format_price(price):
    return f"{price:,}".replace(',', ' ') + ' ₽'

def find_city_code(city_input):
    for city_key, code in CITIES.items():
        if city_input.lower() == city_key.lower():
            return code, city_key
    return city_input.lower().replace(' ', '_'), city_input

def format_ad_message(ad, index=None):
    prefix = f"{index}. " if index is not None else ""
    
    message = (
        f"{prefix}{ad['title']}\n"
        f"Цена: {ad['price']}\n"
        f"Местоположение: {ad['location']}\n"
        f"Дата: {ad['date']}\n"
    )
    
    if ad['link']:
        message += f"Ссылка: {ad['link']}\n"
    
    return message

def validate_price_input(price_text):
    if not price_text or price_text.lower() in ['нет', 'без', 'none']:
        return None
    
    try:
        price = int(price_text.strip())
        return price if price > 0 else None
    except ValueError:
        return None