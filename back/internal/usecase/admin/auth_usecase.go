package admin

import (
	"context"
	"errors"
	"strings"

	"github.com/RomaGrach/quest-bot-backend/internal/domain/auth"
	"github.com/RomaGrach/quest-bot-backend/internal/domain/common"
	"github.com/RomaGrach/quest-bot-backend/internal/security"
)

type AuthUseCase struct {
	repo   auth.Repository
	hasher security.PasswordHasher
	tokens *security.TokenManager
}

func NewAuthUseCase(repo auth.Repository, hasher security.PasswordHasher, tokens *security.TokenManager) *AuthUseCase {
	return &AuthUseCase{
		repo:   repo,
		hasher: hasher,
		tokens: tokens,
	}
}

type LoginInput struct {
	Username string
	Password string
}

type LoginResult struct {
	Token    string `json:"token"`
	Username string `json:"username"`
	Role     string `json:"role"`
}

func (uc *AuthUseCase) Login(ctx context.Context, in LoginInput) (LoginResult, error) {
	if strings.TrimSpace(in.Username) == "" || strings.TrimSpace(in.Password) == "" {
		return LoginResult{}, common.ErrValidation
	}

	adminUser, err := uc.repo.GetByUsername(ctx, in.Username)
	if err != nil {
		if errors.Is(err, common.ErrNotFound) {
			return LoginResult{}, common.ErrUnauthorized
		}
		return LoginResult{}, err
	}

	if !uc.hasher.Compare(adminUser.PasswordHash, in.Password) {
		return LoginResult{}, common.ErrUnauthorized
	}

	token, err := uc.tokens.Issue(adminUser.ID, adminUser.Username, string(adminUser.Role))
	if err != nil {
		return LoginResult{}, err
	}

	return LoginResult{
		Token:    token,
		Username: adminUser.Username,
		Role:     string(adminUser.Role),
	}, nil
}
