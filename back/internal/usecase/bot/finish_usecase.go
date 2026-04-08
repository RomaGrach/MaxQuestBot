package bot

import (
	"context"
	"errors"

	"github.com/RomaGrach/quest-bot-backend/internal/domain/attempt"
	"github.com/RomaGrach/quest-bot-backend/internal/domain/common"
	"github.com/RomaGrach/quest-bot-backend/internal/domain/quest"
	"github.com/RomaGrach/quest-bot-backend/internal/domain/question"
	"github.com/RomaGrach/quest-bot-backend/internal/domain/user"
)

type FinishUseCase struct {
	users     user.Repository
	quests    quest.Repository
	attempts  attempt.Repository
	questions question.Repository
}

func NewFinishUseCase(
	users user.Repository,
	quests quest.Repository,
	attempts attempt.Repository,
	questions question.Repository,
) *FinishUseCase {
	return &FinishUseCase{
		users:     users,
		quests:    quests,
		attempts:  attempts,
		questions: questions,
	}
}

type QuestState struct {
	Attempt         attempt.Attempt    `json:"attempt"`
	CurrentQuestion *question.Question `json:"current_question,omitempty"`
	Completed       bool               `json:"completed"`
	PrizeInfo       string             `json:"prize_info,omitempty"`
}

func (uc *FinishUseCase) Execute(ctx context.Context, maxUserID string, questID int64) (QuestState, error) {
	u, err := uc.users.GetByMaxUserID(ctx, maxUserID)
	if err != nil {
		if errors.Is(err, common.ErrNotFound) {
			return QuestState{}, common.ErrUnauthorized
		}
		return QuestState{}, err
	}
	q, err := uc.quests.GetByID(ctx, questID)
	if err != nil {
		return QuestState{}, err
	}
	a, err := uc.attempts.GetByUserAndQuest(ctx, u.ID, questID)
	if err != nil {
		return QuestState{}, err
	}
	if a.Status == attempt.StatusCompleted {
		return QuestState{
			Attempt:   a,
			Completed: true,
			PrizeInfo: q.PrizeInfo,
		}, nil
	}
	current, err := uc.questions.GetByQuestAndOrder(ctx, questID, a.CurrentQuestionOrder)
	if err != nil {
		return QuestState{}, err
	}
	return QuestState{
		Attempt:         a,
		CurrentQuestion: &current,
		Completed:       false,
	}, nil
}
