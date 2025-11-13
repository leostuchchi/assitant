-- Таблица для кэширования AI рекомендаций
CREATE TABLE ai_recommendations (
    telegram_id BIGINT REFERENCES users(telegram_id) ON DELETE CASCADE,
    target_date DATE NOT NULL,
    data_hash VARCHAR(64) NOT NULL,  -- Хэш входных данных для инвалидации
    recommendations TEXT NOT NULL,
    model_version VARCHAR(20) DEFAULT 'llama3.1:8b',
    prompt_tokens INTEGER,
    completion_tokens INTEGER,
    response_time_ms INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (telegram_id, target_date)
);

-- Индексы для быстрого поиска
CREATE INDEX idx_ai_recommendations_hash ON ai_recommendations(data_hash);
CREATE INDEX idx_ai_recommendations_date ON ai_recommendations(target_date);
CREATE INDEX idx_ai_recommendations_created ON ai_recommendations(created_at);

-- Таблица для пре-обработанных астрологических инсайтов
CREATE TABLE astro_insights (
    telegram_id BIGINT PRIMARY KEY REFERENCES users(telegram_id) ON DELETE CASCADE,
    dominant_energy JSONB NOT NULL,
    personality_traits JSONB NOT NULL,
    planetary_strengths JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- Добавляем поле для хранения хэша данных в natal_predictions
ALTER TABLE natal_predictions ADD COLUMN data_hash VARCHAR(64);

-- Индекс для быстрой проверки актуальности
CREATE INDEX idx_predictions_hash ON natal_predictions(data_hash);



