-- Инициализация оптимизированной схемы БД для проекта Astra

-- Таблица пользователей (без изменений)
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

-- Таблица натальных карт (переименована для ясности)
CREATE TABLE IF NOT EXISTS user_astro_profile (
    telegram_id BIGINT PRIMARY KEY REFERENCES users(telegram_id) ON DELETE CASCADE,
    natal_chart_data JSONB NOT NULL,
    psyho_matrix_data JSONB NOT NULL,
    dominant_energy VARCHAR(50),
    personality_traits JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- УДАЛЕНА: Таблица психоматриц (данные перенесены в user_astro_profile)

-- ОПТИМИЗИРОВАННАЯ: Таблица ежедневных расчетов (вместо natal_predictions)
CREATE TABLE IF NOT EXISTS daily_calculations (
    telegram_id BIGINT REFERENCES users(telegram_id) ON DELETE CASCADE,
    target_date DATE NOT NULL,
    biorhythm_data JSONB NOT NULL,
    astro_transits_data JSONB NOT NULL,
    calculation_metadata JSONB NOT NULL DEFAULT '{}',
    data_hash VARCHAR(64) NOT NULL,
    calculation_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (telegram_id, target_date)
);

-- Таблица биоритмов (сохранена для обратной совместимости)
CREATE TABLE IF NOT EXISTS biorhythms (
    telegram_id BIGINT REFERENCES users(telegram_id) ON DELETE CASCADE,
    biorhythm_data JSONB NOT NULL,
    calculation_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (telegram_id, calculation_date)
);

-- НОВАЯ: Таблица кэша расчетов для производительности
CREATE TABLE IF NOT EXISTS calculation_cache (
    telegram_id BIGINT REFERENCES users(telegram_id) ON DELETE CASCADE,
    target_date DATE NOT NULL,
    data_type VARCHAR(20) NOT NULL,
    calculation_data JSONB NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (telegram_id, target_date, data_type)
);

-- УДАЛЕНЫ: Таблицы AI рекомендаций и астрологических инсайтов
-- DROP TABLE IF EXISTS ai_recommendations;
-- DROP TABLE IF EXISTS astro_insights;

-- ОПТИМИЗИРОВАННЫЕ ИНДЕКСЫ:

-- Индексы для users
CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id);
CREATE INDEX IF NOT EXISTS idx_users_birth_date ON users(birth_date);
CREATE INDEX IF NOT EXISTS idx_users_profession ON users(profession);
CREATE INDEX IF NOT EXISTS idx_users_gender ON users(gender);

-- Индексы для астропрофиля
CREATE INDEX IF NOT EXISTS idx_astro_profile_telegram_id ON user_astro_profile(telegram_id);

-- ВЫСОКОЭФФЕКТИВНЫЕ индексы для daily_calculations
CREATE INDEX IF NOT EXISTS idx_daily_calc_target_date ON daily_calculations(target_date);
CREATE INDEX IF NOT EXISTS idx_daily_calc_telegram_date ON daily_calculations(telegram_id, target_date);
CREATE INDEX IF NOT EXISTS idx_daily_calc_hash ON daily_calculations(data_hash);
CREATE INDEX IF NOT EXISTS idx_daily_calc_timestamp ON daily_calculations(calculation_timestamp);

-- Индексы для биоритмов
CREATE INDEX IF NOT EXISTS idx_biorhythms_telegram_id ON biorhythms(telegram_id);
CREATE INDEX IF NOT EXISTS idx_biorhythms_calculation_date ON biorhythms(calculation_date);
CREATE INDEX IF NOT EXISTS idx_biorhythms_composite ON biorhythms(telegram_id, calculation_date);

-- Индексы для кэша
CREATE INDEX IF NOT EXISTS idx_cache_telegram_date ON calculation_cache(telegram_id, target_date);
CREATE INDEX IF NOT EXISTS idx_cache_expires ON calculation_cache(expires_at);
CREATE INDEX IF NOT EXISTS idx_cache_type ON calculation_cache(data_type);

-- Права для пользователя
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO pers_assist;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO pers_assist;

-- Комментарии к таблицам
COMMENT ON TABLE users IS 'Основная таблица пользователей проекта Astra';
COMMENT ON TABLE user_astro_profile IS 'Статические астрологические данные пользователя (натальная карта + психоматрица)';
COMMENT ON TABLE daily_calculations IS 'Ежедневные расчеты для конкретных дат (биоритмы + транзиты)';
COMMENT ON TABLE biorhythms IS 'Исторические данные биоритмов (для обратной совместимости)';
COMMENT ON TABLE calculation_cache IS 'Кэш расчетов для оптимизации производительности';

-- Миграция данных из старых таблиц (если существуют)
DO $$ 
BEGIN
    -- Миграция натальных карт
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'user_natal_charts') THEN
        INSERT INTO user_astro_profile (telegram_id, natal_chart_data, psyho_matrix_data)
        SELECT 
            unc.telegram_id,
            unc.natal_data as natal_chart_data,
            COALESCE(pm.matrix_data, '{}'::JSONB) as psyho_matrix_data
        FROM user_natal_charts unc
        LEFT JOIN psyho_matrix pm ON unc.telegram_id = pm.telegram_id
        ON CONFLICT (telegram_id) DO NOTHING;
        
        RAISE NOTICE '✅ Данные натальных карт и психоматриц мигрированы в user_astro_profile';
    END IF;

    -- Миграция предсказаний в daily_calculations
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'natal_predictions') THEN
        INSERT INTO daily_calculations (telegram_id, target_date, biorhythm_data, astro_transits_data, data_hash)
        SELECT 
            np.telegram_id,
            (np.predictions->>'target_date')::DATE as target_date,
            COALESCE(np.predictions->'daily_calculations'->'biorhythm_data', '{}'::JSONB) as biorhythm_data,
            COALESCE(np.predictions->'daily_calculations'->'astro_data', '{}'::JSONB) as astro_transits_data,
            COALESCE(np.data_hash, md5(np.predictions::text)) as data_hash
        FROM natal_predictions np
        WHERE np.predictions ? 'target_date'
        ON CONFLICT (telegram_id, target_date) DO NOTHING;
        
        RAISE NOTICE '✅ Данные предсказаний мигрированы в daily_calculations';
    END IF;

EXCEPTION
    WHEN others THEN
        RAISE NOTICE '⚠️ Миграция данных пропущена: %', SQLERRM;
END $$;

-- Удаление старых таблиц после успешной миграции
DROP TABLE IF EXISTS psyho_matrix CASCADE;
DROP TABLE IF EXISTS user_natal_charts CASCADE;
DROP TABLE IF EXISTS natal_predictions CASCADE;
DROP TABLE IF EXISTS ai_recommendations CASCADE;
DROP TABLE IF EXISTS astro_insights CASCADE;

-- Логирование успешной инициализации
DO $$ 
BEGIN
    RAISE NOTICE '🎉 База данных Astra успешно инициализирована с оптимизированной схемой';
    RAISE NOTICE '📊 Таблицы: users, user_astro_profile, daily_calculations, biorhythms, calculation_cache';
    RAISE NOTICE '⚡ Индексы оптимизированы для быстрых запросов по датам';
END $$;

-- Только добавление полей (обратно совместимо)
ALTER TABLE daily_calculations ADD COLUMN ml_features JSONB;
ALTER TABLE daily_calculations ADD COLUMN basic_insights JSONB;
-- БЕЗ новых таблиц, БЕЗ миграций данных

