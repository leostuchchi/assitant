
-- Таблица пользователей
CREATE TABLE users (
    telegram_id BIGINT PRIMARY KEY,
    birth_date DATE NOT NULL,
    birth_time TIME NOT NULL,
    birth_city VARCHAR(100) NOT NULL,
    profession VARCHAR(100),
    job_position VARCHAR(100),
    current_city VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Обновляем таблицу натальных карт
CREATE TABLE user_natal_charts (
    telegram_id BIGINT PRIMARY KEY REFERENCES users(telegram_id) ON DELETE CASCADE,
    natal_data JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица психоматриц (нумерология)
CREATE TABLE psyho_matrix (
    telegram_id BIGINT PRIMARY KEY REFERENCES users(telegram_id) ON DELETE CASCADE,
    matrix_data JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица предсказаний (оставляем как есть)
CREATE TABLE natal_predictions (
    telegram_id BIGINT PRIMARY KEY REFERENCES users(telegram_id) ON DELETE CASCADE,
    predictions JSONB NOT NULL,
    assistant_data JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Создаем индексы
CREATE INDEX idx_users_telegram_id ON users(telegram_id);
CREATE INDEX idx_users_birth_date ON users(birth_date);
CREATE INDEX idx_user_natal_charts_telegram_id ON user_natal_charts(telegram_id);
CREATE INDEX idx_psyho_matrix_telegram_id ON psyho_matrix(telegram_id);
CREATE INDEX idx_natal_predictions_telegram_id ON natal_predictions(telegram_id);

-- Даем права пользователю
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO pers_assist;

select * from psyho_matrix


-- Таблица для биоритмов
CREATE TABLE biorhythms (
    telegram_id BIGINT PRIMARY KEY REFERENCES users(telegram_id) ON DELETE CASCADE,
    biorhythm_data JSONB NOT NULL,
    calculation_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Индекс для быстрого поиска
CREATE INDEX idx_biorhythms_telegram_id ON biorhythms(telegram_id);
CREATE INDEX idx_biorhythms_calculation_date ON biorhythms(calculation_date);
