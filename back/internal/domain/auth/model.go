package auth

import "github.com/RomaGrach/quest-bot-backend/internal/domain/common"

type Admin struct {
	ID           int64       `json:"id"`
	Username     string      `json:"username"`
	PasswordHash string      `json:"-"`
	Role         common.Role `json:"role"`
}
