package bot

import (
	"context"
	"errors"
	"strings"

	"github.com/RomaGrach/quest-bot-backend/internal/domain/common"
	"github.com/RomaGrach/quest-bot-backend/internal/domain/user"
)

type RegistrationUseCase struct {
	users user.Repository
}

func NewRegistrationUseCase(users user.Repository) *RegistrationUseCase {
	return &RegistrationUseCase{users: users}
}

type RegisterInput struct {
	MaxUserID string
	Phone     string
	Consent   bool
}

func (uc *RegistrationUseCase) Execute(ctx context.Context, in RegisterInput) (user.User, error) {
	if strings.TrimSpace(in.MaxUserID) == "" {
		return user.User{}, common.ErrValidation
	}
	if !in.Consent {
		return user.User{}, common.ErrValidation
	}

	existing, err := uc.users.GetByMaxUserID(ctx, in.MaxUserID)
	if err == nil {
		existing.Phone = user.NormalizePhone(in.Phone)
		existing.Consent = in.Consent
		return uc.users.Update(ctx, existing)
	}
	if !errors.Is(err, common.ErrNotFound) {
		return user.User{}, err
	}

	return uc.users.Create(ctx, user.User{
		MaxUserID: in.MaxUserID,
		Phone:     user.NormalizePhone(in.Phone),
		Consent:   in.Consent,
	})
}
