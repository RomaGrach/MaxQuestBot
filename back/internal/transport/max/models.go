package max

type IncomingEvent struct {
	Type    string `json:"type"`
	UserID  string `json:"user_id"`
	ChatID  string `json:"chat_id"`
	Text    string `json:"text"`
	EventID string `json:"event_id"`
}
