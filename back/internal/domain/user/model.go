package user

import "time"

type User struct {
	ID           int64     `json:"id"`
	MaxUserID    string    `json:"max_user_id"`
	Phone        string    `json:"phone,omitempty"`
	Consent      bool      `json:"consent"`
	Comment      string    `json:"comment,omitempty"`
	RegisteredAt time.Time `json:"registered_at"`
}
