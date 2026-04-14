package question

type Question struct {
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
