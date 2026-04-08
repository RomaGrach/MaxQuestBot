package bot

import (
	"context"
	"errors"
	"time"

	"github.com/RomaGrach/quest-bot-backend/internal/domain/attempt"
	"github.com/RomaGrach/quest-bot-backend/internal/domain/common"
	"github.com/RomaGrach/quest-bot-backend/internal/domain/quest"
	"github.com/RomaGrach/quest-bot-backend/internal/domain/question"
	"github.com/RomaGrach/quest-bot-backend/internal/domain/user"
)

type StartQuestUseCase struct {
	users     user.Repository
	quests    quest.Repository
	questions question.Repository
	attempts  attempt.Repository
}

func NewStartQuestUseCase(
	users user.Repository,
	quests quest.Repository,
	questions question.Repository,
	attempts attempt.Repository,
) *StartQuestUseCase {
	return &StartQuestUseCase{
		users:     users,
		quests:    quests,
		questions: questions,
		attempts:  attempts,
	}
}

type StartQuestInput struct {
	MaxUserID string
	QuestID   int64
}

type StartQuestResult struct {
	Quest           quest.Quest       `json:"quest"`
	Attempt         attempt.Attempt   `json:"attempt"`
	CurrentQuestion question.Question `json:"current_question"`
}

func (uc *StartQuestUseCase) Execute(ctx context.Context, in StartQuestInput) (StartQuestResult, error) {
	u, err := uc.users.GetByMaxUserID(ctx, in.MaxUserID)
	if err != nil {
		if errors.Is(err, common.ErrNotFound) {
			return StartQuestResult{}, common.ErrUnauthorized
		}
		return StartQuestResult{}, err
	}

	q, err := uc.quests.GetByID(ctx, in.QuestID)
	if err != nil {
		return StartQuestResult{}, err
	}
	if !quest.IsAvailable(q, time.Now()) {
		return StartQuestResult{}, common.ErrForbidden
	}

	firstQuestion, err := uc.questions.GetByQuestAndOrder(ctx, in.QuestID, 1)
	if err != nil {
		return StartQuestResult{}, err
	}

	activeAttempt, err := uc.attempts.GetActiveByUserID(ctx, u.ID)
	if err == nil && activeAttempt.QuestID != in.QuestID {
		return StartQuestResult{}, common.ErrConflict
	}
	if err != nil && !errors.Is(err, common.ErrNotFound) {
		return StartQuestResult{}, err
	}

	lastAttempt, err := uc.attempts.GetByUserAndQuest(ctx, u.ID, in.QuestID)
	if err == nil {
		if lastAttempt.GiftIssued() {
			return StartQuestResult{}, common.ErrForbidden
		}
		if lastAttempt.Status == attempt.StatusCompleted && !q.AllowRetryBeforeGift {
			return StartQuestResult{}, common.ErrConflict
		}
		if lastAttempt.Status == attempt.StatusInProgress {
			current, getErr := uc.questions.GetByQuestAndOrder(ctx, in.QuestID, lastAttempt.CurrentQuestionOrder)
			if getErr != nil {
				return StartQuestResult{}, getErr
			}
			return StartQuestResult{
				Quest:           q,
				Attempt:         lastAttempt,
				CurrentQuestion: current,
			}, nil
		}
	}
	if err != nil && !errors.Is(err, common.ErrNotFound) {
		return StartQuestResult{}, err
	}

	created, err := uc.attempts.Create(ctx, attempt.Attempt{
		UserID:               u.ID,
		QuestID:              in.QuestID,
		Status:               attempt.StatusInProgress,
		CurrentQuestionOrder: 1,
		AttemptsByQuestion:   make(map[int]int),
		StartedAt:            time.Now(),
	})
	if err != nil {
		return StartQuestResult{}, err
	}

	return StartQuestResult{
		Quest:           q,
		Attempt:         created,
		CurrentQuestion: firstQuestion,
	}, nil
}
