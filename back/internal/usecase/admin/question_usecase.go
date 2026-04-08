package admin

import (
	"context"
	"strings"

	"github.com/RomaGrach/quest-bot-backend/internal/domain/common"
	"github.com/RomaGrach/quest-bot-backend/internal/domain/question"
)

type QuestionUseCase struct {
	repo question.Repository
}

func NewQuestionUseCase(repo question.Repository) *QuestionUseCase {
	return &QuestionUseCase{repo: repo}
}

func (uc *QuestionUseCase) ListByQuest(ctx context.Context, questID int64) ([]question.Question, error) {
	if questID == 0 {
		return nil, common.ErrValidation
	}
	return uc.repo.ListByQuestID(ctx, questID)
}

func (uc *QuestionUseCase) Create(ctx context.Context, q question.Question) (question.Question, error) {
	if q.QuestID == 0 || q.Order <= 0 || strings.TrimSpace(q.Task) == "" || strings.TrimSpace(q.CorrectAnswer) == "" {
		return question.Question{}, common.ErrValidation
	}
	return uc.repo.Create(ctx, q)
}

func (uc *QuestionUseCase) Update(ctx context.Context, q question.Question) (question.Question, error) {
	if q.ID == 0 || q.QuestID == 0 || q.Order <= 0 {
		return question.Question{}, common.ErrValidation
	}
	return uc.repo.Update(ctx, q)
}

func (uc *QuestionUseCase) Delete(ctx context.Context, questionID int64) error {
	if questionID == 0 {
		return common.ErrValidation
	}
	return uc.repo.Delete(ctx, questionID)
}
