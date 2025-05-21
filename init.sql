CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR UNIQUE NOT NULL,
    password VARCHAR NOT NULL
);

CREATE TABLE IF NOT EXISTS posts (
    uid VARCHAR PRIMARY KEY,
    post_url TEXT,
    video_url TEXT,
    image_url TEXT,
    comments INT,
    reactions INT,
    category VARCHAR
);

-- admin1 密碼: 1minda（bcrypt hash）
INSERT INTO users (username, password)
VALUES 
('admin1', '$2b$12$Df8lGJISWxKpJ6NgZz6j/evWrr1F57KLEUeRJjX.SJP3XHRCGE4nC'),
('admin2', '$2b$12$1fBz9WqLd1E2phnNHFAo0u0iz3KrWwhe3A6HEbpDY.4jc.xZ0OYRe')
ON CONFLICT DO NOTHING;
