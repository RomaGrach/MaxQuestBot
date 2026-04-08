package quest

import "time"

type Status string

const (
	StatusDraft     Status = "draft"
	StatusPublished Status = "published"
	StatusArchived  Status = "archived"
)

type Quest struct {
	ID                   int64      `json:"id"`
	Title                string     `json:"title"`
	Description          string     `json:"description"`
	Status               Status     `json:"status"`
	StartPoint           string     `json:"start_point"`
	PrizeInfo            string     `json:"prize_info"`
	StartAt              *time.Time `json:"start_at,omitempty"`
	EndAt                *time.Time `json:"end_at,omitempty"`
	DefaultMaxAttempts   int        `json:"default_max_attempts"`
	AllowRetryBeforeGift bool       `json:"allow_retry_before_gift"`
	CreatedAt            time.Time  `json:"created_at"`
	UpdatedAt            time.Time  `json:"updated_at"`
}
