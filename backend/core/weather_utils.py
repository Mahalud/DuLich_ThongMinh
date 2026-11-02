WEATHER_PREFERENCES = {
    # Balanced keeps the proposal's 15–24–30–40 °C trapezoid and 0.5/0.3/0.2 weights.
    'balanced': {'temperature_points': (15, 24, 30, 40), 'weights': (0.5, 0.3, 0.2)},
    # Cool shifts the temperature peak toward mild days; rain and wind memberships stay unchanged.
    'cool': {'temperature_points': (12, 16, 24, 30), 'weights': (0.5, 0.3, 0.2)},
    # Warm prefers warmer days while retaining balanced rain and wind weights.
    'warm': {'temperature_points': (24, 28, 33, 40), 'weights': (0.5, 0.3, 0.2)},
    # Dry gives rain likelihood the largest share; all three weights still sum to one.
    'dry': {'temperature_points': (15, 24, 30, 40), 'weights': (0.3, 0.5, 0.2)},
}

WEATHER_PREFERENCE_LABELS = {
    'balanced': 'Mặc định',
    'cool': 'Mát mẻ',
    'warm': 'Nắng ấm',
    'dry': 'Ít mưa',
}


def weather_cache_key(latitude, longitude, target_date):
    """One v3 key per place and date; preferences are deliberately excluded."""
    if hasattr(target_date, 'isoformat'):
        target_date = target_date.isoformat()
    return f'weather:v3:{latitude}:{longitude}:{target_date}'


def weather_score_body(target_date, temperature, precipitation, wind_speed):
    """Build the raw Open-Meteo daily values shared by every preference."""
    return {
        'date': str(target_date),
        'temperature_c': round(float(temperature), 1),
        'rain_probability': round(float(precipitation), 1),
        'wind_kmh': round(float(wind_speed), 1),
        'weather_available': True,
    }


def unavailable_weather_body(target_date):
    return {
        'date': str(target_date),
        'temperature_c': None,
        'rain_probability': None,
        'wind_kmh': None,
        'weather_available': False,
    }


def _weather_summary(temperature, precipitation, wind_speed):
    if temperature >= 32:
        temperature_text = 'Ấm nóng'
    elif temperature >= 24:
        temperature_text = 'Ấm áp'
    elif temperature >= 17:
        temperature_text = 'Dịu mát'
    else:
        temperature_text = 'Trời lạnh'

    if precipitation <= 20:
        rain_text = 'ít mưa'
    elif precipitation <= 50:
        rain_text = 'mưa nhẹ'
    else:
        rain_text = 'khả năng mưa cao'
    if wind_speed >= 35:
        return f'{temperature_text}, {rain_text}, gió mạnh'
    return f'{temperature_text}, {rain_text}'


def calculate_weather_score(raw_weather, weather_preference='balanced'):
    """Score raw forecast data at response time; cached values never contain scores."""
    preference = weather_preference if weather_preference in WEATHER_PREFERENCES else 'balanced'
    if not raw_weather or not raw_weather.get('weather_available', True):
        return {
            'date': (raw_weather or {}).get('date'),
            'temperature': None,
            'precipitation_probability': None,
            'wind_speed': None,
            'weather': {
                'temperature_c': None, 'rain_probability': None, 'wind_kmh': None,
                'summary': 'Chưa có dữ liệu thời tiết',
            },
            'weather_score': 0.5,
            'temperature_membership': 0.5,
            'rain_membership': 0.5,
            'wind_membership': 0.5,
            'weather_available': False,
        }

    temperature = float(raw_weather['temperature_c'])
    precipitation = float(raw_weather['rain_probability'])
    wind_speed = float(raw_weather['wind_kmh'])
    from .views import _member_trapezoid

    config = WEATHER_PREFERENCES[preference]
    temperature_membership = _member_trapezoid(temperature, *config['temperature_points'])
    rain_membership = max(0.0, min(1.0, 1 - precipitation / 100))
    wind_membership = max(0.0, min(1.0, 1 - wind_speed / 60))
    temperature_weight, rain_weight, wind_weight = config['weights']
    score = temperature_weight * temperature_membership + rain_weight * rain_membership + wind_weight * wind_membership
    weather = {
        'temperature_c': temperature,
        'rain_probability': precipitation,
        'wind_kmh': wind_speed,
        'summary': _weather_summary(temperature, precipitation, wind_speed),
    }
    return {
        'date': raw_weather.get('date'),
        'temperature': temperature,
        'precipitation_probability': precipitation,
        'wind_speed': wind_speed,
        'weather': weather,
        'weather_score': round(score, 4),
        'temperature_membership': round(temperature_membership, 4),
        'rain_membership': round(rain_membership, 4),
        'wind_membership': round(wind_membership, 4),
        'weather_available': True,
    }
