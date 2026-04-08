package dto

type RegisterRequest struct {
	MaxUserID string `json:"max_user_id"`
	Phone     string `json:"phone"`
	Consent   bool   `json:"consent"`
}

type StartQuestRequest struct {
	MaxUserID string `json:"max_user_id"`
}

type AnswerRequest struct {
	MaxUserID string `json:"max_user_id"`
	Answer    string `json:"answer"`
}

type HintRequest struct {
	MaxUserID string `json:"max_user_id"`
}
