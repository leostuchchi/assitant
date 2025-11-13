-- Инициализация таблиц при первом запуске контейнера

-- Таблица пользователей
CREATE TABLE IF NOT EXISTS users (
    telegram_id BIGINT PRIMARY KEY,
    birth_date DATE NOT NULL,
    birth_time TIME NOT NULL,
    birth_city VARCHAR(100) NOT NULL,
    profession VARCHAR(100),
    job_position VARCHAR(100),
    current_city VARCHAR(100),
    gender VARCHAR(10),
    request_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица натальных карт
CREATE TABLE IF NOT EXISTS user_natal_charts (
    telegram_id BIGINT PRIMARY KEY REFERENCES users(telegram_id) ON DELETE CASCADE,
    natal_data JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица психоматриц
CREATE TABLE IF NOT EXISTS psyho_matrix (
    telegram_id BIGINT PRIMARY KEY REFERENCES users(telegram_id) ON DELETE CASCADE,
    matrix_data JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица предсказаний
CREATE TABLE IF NOT EXISTS natal_predictions (
    telegram_id BIGINT PRIMARY KEY REFERENCES users(telegram_id) ON DELETE CASCADE,
    predictions JSONB NOT NULL,
    assistant_data JSONB NOT NULL DEFAULT '{}',
    data_hash VARCHAR(64),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица биоритмов
CREATE TABLE IF NOT EXISTS biorhythms (
    telegram_id BIGINT REFERENCES users(telegram_id) ON DELETE CASCADE,
    biorhythm_data JSONB NOT NULL,
    calculation_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (telegram_id, calculation_date)
);

-- НОВЫЕ ТАБЛИЦЫ ДЛЯ AI РЕКОМЕНДАЦИЙ:

-- Таблица для кэширования AI рекомендаций
CREATE TABLE IF NOT EXISTS ai_recommendations (
    telegram_id BIGINT REFERENCES users(telegram_id) ON DELETE CASCADE,
    target_date DATE NOT NULL,
    data_hash VARCHAR(64) NOT NULL,
    recommendations TEXT NOT NULL,
    model_version VARCHAR(20) DEFAULT 'llama3.1:8b',
    prompt_tokens INTEGER,
    completion_tokens INTEGER,
    response_time_ms INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (telegram_id, target_date)
);

-- Таблица для пре-обработанных астрологических инсайтов
CREATE TABLE IF NOT EXISTS astro_insights (
    telegram_id BIGINT PRIMARY KEY REFERENCES users(telegram_id) ON DELETE CASCADE,
    dominant_energy JSONB NOT NULL,
    personality_traits JSONB NOT NULL,
    planetary_strengths JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- СОЗДАНИЕ ИНДЕКСОВ ДЛЯ ПРОИЗВОДИТЕЛЬНОСТИ:

-- Индексы для users
CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id);
CREATE INDEX IF NOT EXISTS idx_users_birth_date ON users(birth_date);
CREATE INDEX IF NOT EXISTS idx_users_profession ON users(profession);

-- Индексы для натальных карт
CREATE INDEX IF NOT EXISTS idx_user_natal_charts_telegram_id ON user_natal_charts(telegram_id);

-- Индексы для психоматриц
CREATE INDEX IF NOT EXISTS idx_psyho_matrix_telegram_id ON psyho_matrix(telegram_id);

-- Индексы для предсказаний
CREATE INDEX IF NOT EXISTS idx_natal_predictions_telegram_id ON natal_predictions(telegram_id);
CREATE INDEX IF NOT EXISTS idx_natal_predictions_hash ON natal_predictions(data_hash);

-- Индексы для биоритмов
CREATE INDEX IF NOT EXISTS idx_biorhythms_telegram_id ON biorhythms(telegram_id);
CREATE INDEX IF NOT EXISTS idx_biorhythms_calculation_date ON biorhythms(calculation_date);

-- Индексы для AI рекомендаций
CREATE INDEX IF NOT EXISTS idx_ai_recommendations_hash ON ai_recommendations(data_hash);
CREATE INDEX IF NOT EXISTS idx_ai_recommendations_date ON ai_recommendations(target_date);
CREATE INDEX IF NOT EXISTS idx_ai_recommendations_created ON ai_recommendations(created_at);

-- Права для пользователя
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO pers_assist;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO pers_assist;

-- Комментарии к таблицам
COMMENT ON TABLE users IS 'Основная таблица пользователей персонального ассистента';
COMMENT ON TABLE ai_recommendations IS 'Кэш AI рекомендаций от модели Llama';
COMMENT ON TABLE astro_insights IS 'Пре-обработанные астрологические инсайты для AI';

-- Логирование успешной инициализации
DO $$ 
BEGIN
    RAISE NOTICE '✅ База данных personal_assistant успешно инициализирована';
END $$;



