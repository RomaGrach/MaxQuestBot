package admin

import (
	"context"
	"time"

	"github.com/RomaGrach/quest-bot-backend/internal/domain/attempt"
	"github.com/RomaGrach/quest-bot-backend/internal/domain/common"
)

type GiftUseCase struct {
	attempts attempt.Repository
}

func NewGiftUseCase(attempts attempt.Repository) *GiftUseCase {
	return &GiftUseCase{attempts: attempts}
}

type MarkGiftInput struct {
	AttemptID     int64
	IssuerAdminID int64
	Comment       string
}

func (uc *GiftUseCase) MarkIssued(ctx context.Context, in MarkGiftInput) (attempt.Attempt, error) {
	if in.AttemptID == 0 || in.IssuerAdminID == 0 {
		return attempt.Attempt{}, common.ErrValidation
	}
	a, err := uc.attempts.GetByID(ctx, in.AttemptID)
	if err != nil {
		return attempt.Attempt{}, err
	}
	if a.Status != attempt.StatusCompleted {
		return attempt.Attempt{}, common.ErrInvalidState
	}
	if a.GiftIssued() {
		return attempt.Attempt{}, common.ErrConflict
	}
	now := time.Now()
	a.GiftIssuedAt = &now
	a.GiftIssuedByAdminID = &in.IssuerAdminID
	a.GiftComment = in.Comment
	return uc.attempts.Update(ctx, a)
}
