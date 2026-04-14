package dto

import "time"

type AdminLoginRequest struct {
	Username string `json:"username"`
	Password string `json:"password"`
}

type AdminLoginResponse struct {
	Token    string `json:"token"`
	Username string `json:"username"`
	Role     string `json:"role"`
}

type CreateQuestRequest struct {
	Title                string     `json:"title"`
	Description          string     `json:"description"`
	Status               string     `json:"status"`
	StartPoint           string     `json:"start_point"`
	PrizeInfo            string     `json:"prize_info"`
	StartAt              *time.Time `json:"start_at,omitempty"`
	EndAt                *time.Time `json:"end_at,omitempty"`
	DefaultMaxAttempts   int        `json:"default_max_attempts"`
	AllowRetryBeforeGift bool       `json:"allow_retry_before_gift"`
}

type UpdateQuestRequest struct {
	ID                   int64      `json:"id"`
	Title                string     `json:"title"`
	Description          string     `json:"description"`
	Status               string     `json:"status"`
	StartPoint           string     `json:"start_point"`
	PrizeInfo            string     `json:"prize_info"`
	StartAt              *time.Time `json:"start_at,omitempty"`
	EndAt                *time.Time `json:"end_at,omitempty"`
	DefaultMaxAttempts   int        `json:"default_max_attempts"`
	AllowRetryBeforeGift bool       `json:"allow_retry_before_gift"`
}

type CreateQuestionRequest struct {
	QuestID           int64   `json:"quest_id"`
	Order             int     `json:"order"`
	Context           string  `json:"context"`
	Task              string  `json:"task"`
	CorrectAnswer     string  `json:"correct_answer"`
	Explanation       string  `json:"explanation"`
	Hint              string  `json:"hint"`
	SemanticMode      string  `json:"semantic_mode"`
	SemanticThreshold float64 `json:"semantic_threshold"`
	MaxAttempts       *int    `json:"max_attempts,omitempty"`
}

type UpdateQuestionRequest struct {
	ID                int64   `json:"id"`
	QuestID           int64   `json:"quest_id"`
	Order             int     `json:"order"`
	Context           string  `json:"context"`
	Task              string  `json:"task"`
	CorrectAnswer     string  `json:"correct_answer"`
	Explanation       string  `json:"explanation"`
	Hint              string  `json:"hint"`
	SemanticMode      string  `json:"semantic_mode"`
	SemanticThreshold float64 `json:"semantic_threshold"`
	MaxAttempts       *int    `json:"max_attempts,omitempty"`
}

type MarkGiftRequest struct {
	Comment string `json:"comment"`
}

type UpdateUserCommentRequest struct {
	Comment string `json:"comment"`
}
