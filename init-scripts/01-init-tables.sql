-- Расширенная таблица пользователей
CREATE TABLE user_profiles (
    telegram_id BIGINT PRIMARY KEY,
    
    -- Основные данные
    birth_data JSONB NOT NULL,
    natal_chart JSONB,
    psyho_matrix JSONB,
    biorhythms JSONB,
    magic_profile JSONB,
    
    -- ✅ ДАННЫЕ ДЛЯ ASSISTANT
    assistant_data JSONB DEFAULT '{
        "optimal_activities": [],
        "energy_scores": {},
        "last_calculated": null
    }',
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- ✅ ТАБЛИЦА АКТИВНОСТЕЙ ДЛЯ ASSISTANT
CREATE TABLE activity_templates (
    id SERIAL PRIMARY KEY,
    category VARCHAR(50) NOT NULL,      -- physical, spiritual, learning, etc.
    name VARCHAR(100) NOT NULL,         -- Название активности
    energy_type VARCHAR(20) NOT NULL,   -- high/medium/low_energy
    description TEXT,
    tags JSONB DEFAULT '[]',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Индексы для оптимизации
CREATE INDEX idx_assistant_activities ON user_profiles 
USING gin ((assistant_data->'optimal_activities'));
CREATE INDEX idx_activity_category ON activity_templates(category);




