package bot

import (
	"context"
	"errors"

	"github.com/RomaGrach/quest-bot-backend/internal/domain/attempt"
	"github.com/RomaGrach/quest-bot-backend/internal/domain/common"
	"github.com/RomaGrach/quest-bot-backend/internal/domain/question"
	"github.com/RomaGrach/quest-bot-backend/internal/domain/user"
)

type HintUseCase struct {
	users     user.Repository
	attempts  attempt.Repository
	questions question.Repository
}

func NewHintUseCase(
	users user.Repository,
	attempts attempt.Repository,
	questions question.Repository,
) *HintUseCase {
	return &HintUseCase{
		users:     users,
		attempts:  attempts,
		questions: questions,
	}
}

type HintResult struct {
	QuestionOrder int    `json:"question_order"`
	Hint          string `json:"hint"`
}

func (uc *HintUseCase) Execute(ctx context.Context, maxUserID string, questID int64) (HintResult, error) {
	u, err := uc.users.GetByMaxUserID(ctx, maxUserID)
	if err != nil {
		if errors.Is(err, common.ErrNotFound) {
			return HintResult{}, common.ErrUnauthorized
		}
		return HintResult{}, err
	}
	a, err := uc.attempts.GetByUserAndQuest(ctx, u.ID, questID)
	if err != nil {
		return HintResult{}, err
	}
	if a.Status != attempt.StatusInProgress {
		return HintResult{}, common.ErrQuestFinished
	}
	current, err := uc.questions.GetByQuestAndOrder(ctx, questID, a.CurrentQuestionOrder)
	if err != nil {
		return HintResult{}, err
	}
	return HintResult{
		QuestionOrder: current.Order,
		Hint:          current.Hint,
	}, nil
}
