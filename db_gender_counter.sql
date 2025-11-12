-- Безопасное обновление таблицы users - добавляем новые поля с значениями по умолчанию
-- Этот скрипт можно запускать многократно - он не сломает существующую БД

-- Добавляем поле gender если его нет
DO $$ 
BEGIN 
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                  WHERE table_name = 'users' AND column_name = 'gender') THEN
        ALTER TABLE users ADD COLUMN gender VARCHAR(10) DEFAULT 'unknown';
        RAISE NOTICE '✅ Поле gender добавлено в таблицу users';
    ELSE
        RAISE NOTICE '✅ Поле gender уже существует в таблице users';
    END IF;
END $$;

-- Добавляем поле request_count если его нет
DO $$ 
BEGIN 
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                  WHERE table_name = 'users' AND column_name = 'request_count') THEN
        ALTER TABLE users ADD COLUMN request_count INTEGER DEFAULT 0;
        RAISE NOTICE '✅ Поле request_count добавлено в таблицу users';
    ELSE
        RAISE NOTICE '✅ Поле request_count уже существует в таблице users';
    END IF;
END $$;

-- Обновляем существующие записи - устанавливаем значения по умолчанию для старых записей
UPDATE users SET gender = 'unknown' WHERE gender IS NULL;
UPDATE users SET request_count = 0 WHERE request_count IS NULL;

-- Делаем поля NOT NULL только после установки значений по умолчания
DO $$ 
BEGIN 
    -- Для gender
    IF EXISTS (SELECT 1 FROM information_schema.columns 
              WHERE table_name = 'users' AND column_name = 'gender' AND is_nullable = 'YES') THEN
        ALTER TABLE users ALTER COLUMN gender SET NOT NULL;
        RAISE NOTICE '✅ Поле gender установлено как NOT NULL';
    END IF;
    
    -- Для request_count  
    IF EXISTS (SELECT 1 FROM information_schema.columns 
              WHERE table_name = 'users' AND column_name = 'request_count' AND is_nullable = 'YES') THEN
        ALTER TABLE users ALTER COLUMN request_count SET NOT NULL;
        RAISE NOTICE '✅ Поле request_count установлено как NOT NULL';
    END IF;
END $$;

-- Проверяем конечную структуру таблицы
SELECT 
    column_name, 
    data_type, 
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_name = 'users' 
ORDER BY ordinal_position;

select * from users

--delete from users




