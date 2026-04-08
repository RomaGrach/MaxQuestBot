package admin

import (
	"context"
	"strings"
	"time"

	"github.com/RomaGrach/quest-bot-backend/internal/domain/common"
	"github.com/RomaGrach/quest-bot-backend/internal/domain/quest"
)

type QuestUseCase struct {
	repo quest.Repository
}

func NewQuestUseCase(repo quest.Repository) *QuestUseCase {
	return &QuestUseCase{repo: repo}
}

func (uc *QuestUseCase) List(ctx context.Context) ([]quest.Quest, error) {
	return uc.repo.List(ctx)
}

func (uc *QuestUseCase) Create(ctx context.Context, q quest.Quest) (quest.Quest, error) {
	if strings.TrimSpace(q.Title) == "" {
		return quest.Quest{}, common.ErrValidation
	}
	if q.DefaultMaxAttempts == 0 {
		q.DefaultMaxAttempts = 3
	}
	if q.Status == "" {
		q.Status = quest.StatusDraft
	}
	now := time.Now()
	q.CreatedAt = now
	q.UpdatedAt = now
	return uc.repo.Create(ctx, q)
}

func (uc *QuestUseCase) Update(ctx context.Context, q quest.Quest) (quest.Quest, error) {
	if q.ID == 0 || strings.TrimSpace(q.Title) == "" {
		return quest.Quest{}, common.ErrValidation
	}
	return uc.repo.Update(ctx, q)
}

func (uc *QuestUseCase) Delete(ctx context.Context, questID int64) error {
	if questID == 0 {
		return common.ErrValidation
	}
	return uc.repo.Delete(ctx, questID)
}
