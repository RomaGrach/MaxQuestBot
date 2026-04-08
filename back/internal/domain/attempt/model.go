package attempt

import "time"

type Status string

const (
	StatusInProgress Status = "in_progress"
	StatusCompleted  Status = "completed"
)

type Attempt struct {
	ID                   int64       `json:"id"`
	UserID               int64       `json:"user_id"`
	QuestID              int64       `json:"quest_id"`
	Status               Status      `json:"status"`
	CurrentQuestionOrder int         `json:"current_question_order"`
	AttemptsByQuestion   map[int]int `json:"-"`
	StartedAt            time.Time   `json:"started_at"`
	CompletedAt          *time.Time  `json:"completed_at,omitempty"`
	GiftIssuedAt         *time.Time  `json:"gift_issued_at,omitempty"`
	GiftIssuedByAdminID  *int64      `json:"gift_issued_by_admin_id,omitempty"`
	GiftComment          string      `json:"gift_comment,omitempty"`
}

func (a Attempt) GiftIssued() bool {
	return a.GiftIssuedAt != nil
}
