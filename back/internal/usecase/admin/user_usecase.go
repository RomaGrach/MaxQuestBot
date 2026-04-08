package admin

import (
	"context"
	"errors"
	"time"

	"github.com/RomaGrach/quest-bot-backend/internal/domain/attempt"
	"github.com/RomaGrach/quest-bot-backend/internal/domain/common"
	"github.com/RomaGrach/quest-bot-backend/internal/domain/quest"
	"github.com/RomaGrach/quest-bot-backend/internal/domain/user"
)

type UserUseCase struct {
	users    user.Repository
	attempts attempt.Repository
	quests   quest.Repository
}

func NewUserUseCase(
	users user.Repository,
	attempts attempt.Repository,
	quests quest.Repository,
) *UserUseCase {
	return &UserUseCase{
		users:    users,
		attempts: attempts,
		quests:   quests,
	}
}

type UserSummary struct {
	ID              int64  `json:"id"`
	MaxUserID       string `json:"max_user_id"`
	Phone           string `json:"phone"`
	CompletedQuests int    `json:"completed_quests"`
}

type UserAttempt struct {
	AttemptID    int64   `json:"attempt_id"`
	QuestID      int64   `json:"quest_id"`
	QuestTitle   string  `json:"quest_title"`
	Status       string  `json:"status"`
	StartedAt    string  `json:"started_at"`
	CompletedAt  *string `json:"completed_at,omitempty"`
	GiftIssued   bool    `json:"gift_issued"`
	GiftIssuedAt *string `json:"gift_issued_at,omitempty"`
	GiftComment  string  `json:"gift_comment,omitempty"`
}

func (uc *UserUseCase) List(ctx context.Context) ([]UserSummary, error) {
	users, err := uc.users.List(ctx)
	if err != nil {
		return nil, err
	}

	out := make([]UserSummary, 0, len(users))
	for _, u := range users {
		userAttempts, err := uc.attempts.ListByUserID(ctx, u.ID)
		if err != nil {
			return nil, err
		}
		completed := 0
		for _, a := range userAttempts {
			if a.Status == attempt.StatusCompleted {
				completed++
			}
		}
		out = append(out, UserSummary{
			ID:              u.ID,
			MaxUserID:       u.MaxUserID,
			Phone:           u.Phone,
			CompletedQuests: completed,
		})
	}
	return out, nil
}

func (uc *UserUseCase) AttemptsByUser(ctx context.Context, userID int64) ([]UserAttempt, error) {
	attempts, err := uc.attempts.ListByUserID(ctx, userID)
	if err != nil {
		return nil, err
	}

	out := make([]UserAttempt, 0, len(attempts))
	for _, a := range attempts {
		q, err := uc.quests.GetByID(ctx, a.QuestID)
		if err != nil && !errors.Is(err, common.ErrNotFound) {
			return nil, err
		}
		completedAt := formatTimePtr(a.CompletedAt)
		giftIssuedAt := formatTimePtr(a.GiftIssuedAt)
		out = append(out, UserAttempt{
			AttemptID:    a.ID,
			QuestID:      a.QuestID,
			QuestTitle:   q.Title,
			Status:       string(a.Status),
			StartedAt:    a.StartedAt.Format(timeLayout),
			CompletedAt:  completedAt,
			GiftIssued:   a.GiftIssued(),
			GiftIssuedAt: giftIssuedAt,
			GiftComment:  a.GiftComment,
		})
	}
	return out, nil
}

func (uc *UserUseCase) UpdateComment(ctx context.Context, userID int64, comment string) (user.User, error) {
	return uc.users.UpdateComment(ctx, userID, comment)
}

const timeLayout = "2006-01-02T15:04:05Z07:00"

func formatTimePtr(t *time.Time) *string {
	if t == nil {
		return nil
	}
	s := t.Format(timeLayout)
	return &s
}
