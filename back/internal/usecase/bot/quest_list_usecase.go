package bot

import (
	"context"
	"errors"

	"github.com/RomaGrach/quest-bot-backend/internal/domain/common"
	"github.com/RomaGrach/quest-bot-backend/internal/domain/quest"
	"github.com/RomaGrach/quest-bot-backend/internal/domain/user"
)

type QuestListUseCase struct {
	users  user.Repository
	quests quest.Repository
}

func NewQuestListUseCase(users user.Repository, quests quest.Repository) *QuestListUseCase {
	return &QuestListUseCase{
		users:  users,
		quests: quests,
	}
}

func (uc *QuestListUseCase) Execute(ctx context.Context, maxUserID string) ([]quest.Quest, error) {
	if _, err := uc.users.GetByMaxUserID(ctx, maxUserID); err != nil {
		if errors.Is(err, common.ErrNotFound) {
			return nil, common.ErrUnauthorized
		}
		return nil, err
	}

	quests, err := uc.quests.ListPublished(ctx)
	if err != nil {
		return nil, err
	}
	return quests, nil
}
