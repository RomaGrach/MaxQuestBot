CREATE TABLE IF NOT EXISTS admins (
	id BIGSERIAL PRIMARY KEY,
	username TEXT NOT NULL UNIQUE,
	password_hash TEXT NOT NULL,
	role TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS quests (
	id BIGSERIAL PRIMARY KEY,
	title TEXT NOT NULL,
	description TEXT NOT NULL DEFAULT '',
	status TEXT NOT NULL DEFAULT 'draft',
	start_point TEXT NOT NULL DEFAULT '',
	prize_info TEXT NOT NULL DEFAULT '',
	start_at TIMESTAMPTZ,
	end_at TIMESTAMPTZ,
	default_max_attempts INTEGER NOT NULL DEFAULT 3,
	allow_retry_before_gift BOOLEAN NOT NULL DEFAULT FALSE,
	created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
	updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS questions (
	id BIGSERIAL PRIMARY KEY,
	quest_id BIGINT NOT NULL REFERENCES quests(id) ON DELETE CASCADE,
	question_order INTEGER NOT NULL,
	context TEXT NOT NULL DEFAULT '',
	task TEXT NOT NULL,
	correct_answer TEXT NOT NULL,
	explanation TEXT NOT NULL DEFAULT '',
	hint TEXT NOT NULL DEFAULT '',
	semantic_mode TEXT NOT NULL DEFAULT '',
	semantic_threshold DOUBLE PRECISION NOT NULL DEFAULT 0,
	max_attempts INTEGER,
	UNIQUE (quest_id, question_order)
);

CREATE TABLE IF NOT EXISTS users (
	id BIGSERIAL PRIMARY KEY,
	max_user_id TEXT NOT NULL UNIQUE,
	phone TEXT NOT NULL DEFAULT '',
	consent BOOLEAN NOT NULL DEFAULT FALSE,
	comment TEXT NOT NULL DEFAULT '',
	registered_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS quest_attempts (
	id BIGSERIAL PRIMARY KEY,
	user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
	quest_id BIGINT NOT NULL REFERENCES quests(id) ON DELETE CASCADE,
	status TEXT NOT NULL DEFAULT 'in_progress',
	current_question_order INTEGER NOT NULL DEFAULT 1,
	attempts_by_question JSONB NOT NULL DEFAULT '{}' :: jsonb,
	started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
	completed_at TIMESTAMPTZ,
	gift_issued_at TIMESTAMPTZ,
	gift_issued_by_admin_id BIGINT REFERENCES admins(id),
	gift_comment TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS answer_logs (
	id BIGSERIAL PRIMARY KEY,
	attempt_id BIGINT NOT NULL REFERENCES quest_attempts(id) ON DELETE CASCADE,
	question_id BIGINT NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
	answer TEXT NOT NULL,
	is_correct BOOLEAN NOT NULL DEFAULT FALSE,
	created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_questions_quest_id ON questions(quest_id);

CREATE INDEX IF NOT EXISTS idx_attempts_user_id ON quest_attempts(user_id);

CREATE INDEX IF NOT EXISTS idx_attempts_quest_id ON quest_attempts(quest_id);

CREATE INDEX IF NOT EXISTS idx_attempts_active_user ON quest_attempts(user_id, status);

CREATE INDEX IF NOT EXISTS idx_answer_logs_attempt_id ON answer_logs(attempt_id);