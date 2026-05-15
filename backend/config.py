BOT_TOKEN = "8428542909:AAHLv5HrfJKSV0GN9JrUN0_feREnary5yXI"

# Провайдер для платежей (тестовый) - больше не нужен, но оставим для совместимости
PAYMENT_PROVIDER_TOKEN = "632593626:TEST:sandbox_i87891302849"

CITIES = {
    'Все регионы': 'all',
    'Москва': 'moskva',
    'Санкт-Петербург': 'sankt-peterburg',
    'Новосибирск': 'novosibirsk',
    'Екатеринбург': 'ekaterinburg',
    'Казань': 'kazan',
    'Нижний Новгород': 'nizhniy_novgorod',
    'Челябинск': 'chelyabinsk',
    'Самара': 'samara',
    'Омск': 'omsk',
    'Ростов-на-Дону': 'rostov-na-donu',
    'Уфа': 'ufa',
    'Красноярск': 'krasnoyarsk',
    'Воронеж': 'voronezh',
    'Пермь': 'perm',
    'Волгоград': 'volgograd',
    'Краснодар': 'krasnodar',
    'Саратов': 'saratov',
    'Тюмень': 'tyumen',
    'Тольятти': 'tolyatti',
    'Ижевск': 'izhevsk',
    'Барнаул': 'barnaul',
    'Ульяновск': 'ulyanovsk',
    'Иркутск': 'irkutsk',
    'Хабаровск': 'khabarovsk',
    'Ярославль': 'yaroslavl',
    'Владивосток': 'vladivostok'
}

MONITORING_TIMES = {
    '5 минут': 5,
    '15 минут': 15,
    '30 минут': 30,
    '1 час': 60,
    '2 часа': 120,
    '3 часа': 180,
    '4 часа': 240,
    '6 часов': 360,
    '8 часов': 480
}

MONITORING_INTERVALS = {
    '1 минута': 1,
    '2 минуты': 2,
    '5 минут': 5
}

# Настройки парсера
PARSER_SETTINGS = {
    'default_max_items': 200,
    'max_pages': 4,
    'default_timeout': 20,
    'min_sleep': 8,
    'max_sleep': 12
}