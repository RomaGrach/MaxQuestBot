package bot

import (
	"context"
	"errors"
	"strings"
	"time"

	"github.com/RomaGrach/quest-bot-backend/internal/domain/attempt"
	"github.com/RomaGrach/quest-bot-backend/internal/domain/common"
	"github.com/RomaGrach/quest-bot-backend/internal/domain/quest"
	"github.com/RomaGrach/quest-bot-backend/internal/domain/question"
	"github.com/RomaGrach/quest-bot-backend/internal/domain/user"
)

type AnswerUseCase struct {
	users     user.Repository
	quests    quest.Repository
	questions question.Repository
	attempts  attempt.Repository
	matcher   question.Matcher
}

func NewAnswerUseCase(
	users user.Repository,
	quests quest.Repository,
	questions question.Repository,
	attempts attempt.Repository,
	matcher question.Matcher,
) *AnswerUseCase {
	return &AnswerUseCase{
		users:     users,
		quests:    quests,
		questions: questions,
		attempts:  attempts,
		matcher:   matcher,
	}
}

type AnswerInput struct {
	MaxUserID string
	QuestID   int64
	Answer    string
}

type AnswerResult struct {
	AttemptID           int64              `json:"attempt_id"`
	Status              attempt.Status     `json:"status"`
	Correct             bool               `json:"correct"`
	AcceptedByMeaning   bool               `json:"accepted_by_meaning"`
	AttemptsUsed        int                `json:"attempts_used"`
	AttemptsLeft        *int               `json:"attempts_left,omitempty"`
	Hint                string             `json:"hint,omitempty"`
	ShowedCorrectAnswer bool               `json:"showed_correct_answer"`
	CorrectAnswer       string             `json:"correct_answer,omitempty"`
	Explanation         string             `json:"explanation,omitempty"`
	NextQuestion        *question.Question `json:"next_question,omitempty"`
	Completed           bool               `json:"completed"`
	PrizeInfo           string             `json:"prize_info,omitempty"`
}

func (uc *AnswerUseCase) Execute(ctx context.Context, in AnswerInput) (AnswerResult, error) {
	if strings.TrimSpace(in.Answer) == "" {
		return AnswerResult{}, common.ErrValidation
	}

	u, err := uc.users.GetByMaxUserID(ctx, in.MaxUserID)
	if err != nil {
		if errors.Is(err, common.ErrNotFound) {
			return AnswerResult{}, common.ErrUnauthorized
		}
		return AnswerResult{}, err
	}

	q, err := uc.quests.GetByID(ctx, in.QuestID)
	if err != nil {
		return AnswerResult{}, err
	}

	a, err := uc.attempts.GetByUserAndQuest(ctx, u.ID, in.QuestID)
	if err != nil {
		return AnswerResult{}, err
	}
	if a.Status != attempt.StatusInProgress {
		return AnswerResult{}, common.ErrQuestFinished
	}

	current, err := uc.questions.GetByQuestAndOrder(ctx, in.QuestID, a.CurrentQuestionOrder)
	if err != nil {
		return AnswerResult{}, err
	}

	if a.AttemptsByQuestion == nil {
		a.AttemptsByQuestion = make(map[int]int)
	}
	attemptsUsed := a.AttemptsByQuestion[current.Order] + 1
	a.AttemptsByQuestion[current.Order] = attemptsUsed

	maxAttempts := resolveMaxAttempts(q.DefaultMaxAttempts, current.MaxAttempts)
	result := AnswerResult{
		AttemptID:    a.ID,
		AttemptsUsed: attemptsUsed,
	}

	if uc.matcher.Match(in.Answer, current.CorrectAnswer) {
		result.Correct = true
		result.AcceptedByMeaning = !isExact(in.Answer, current.CorrectAnswer)
		result.CorrectAnswer = current.CorrectAnswer
		result.Explanation = current.Explanation
		if err := uc.moveForward(ctx, q, &a, &result); err != nil {
			return AnswerResult{}, err
		}
		return result, nil
	}

	// Неверный ответ.
	result.Hint = current.Hint
	if maxAttempts == 0 || attemptsUsed < maxAttempts {
		if maxAttempts > 0 {
			left := maxAttempts - attemptsUsed
			result.AttemptsLeft = &left
		}
		a.Status = attempt.StatusInProgress
		updated, err := uc.attempts.Update(ctx, a)
		if err != nil {
			return AnswerResult{}, err
		}
		result.Status = updated.Status
		return result, nil
	}

	// Лимит попыток исчерпан: показываем ответ и идем дальше.
	result.ShowedCorrectAnswer = true
	result.CorrectAnswer = current.CorrectAnswer
	result.Explanation = current.Explanation
	if err := uc.moveForward(ctx, q, &a, &result); err != nil {
		return AnswerResult{}, err
	}
	return result, nil
}

func (uc *AnswerUseCase) moveForward(
	ctx context.Context,
	q quest.Quest,
	a *attempt.Attempt,
	result *AnswerResult,
) error {
	nextOrder := a.CurrentQuestionOrder + 1
	nextQuestion, err := uc.questions.GetByQuestAndOrder(ctx, a.QuestID, nextOrder)
	if err == nil {
		a.CurrentQuestionOrder = nextOrder
		a.Status = attempt.StatusInProgress
		updated, updateErr := uc.attempts.Update(ctx, *a)
		if updateErr != nil {
			return updateErr
		}
		result.NextQuestion = &nextQuestion
		result.Status = updated.Status
		return nil
	}
	if !errors.Is(err, common.ErrNotFound) {
		return err
	}

	now := time.Now()
	a.Status = attempt.StatusCompleted
	a.CompletedAt = &now
	updated, updateErr := uc.attempts.Update(ctx, *a)
	if updateErr != nil {
		return updateErr
	}
	result.Completed = true
	result.PrizeInfo = q.PrizeInfo
	result.Status = updated.Status
	return nil
}

func resolveMaxAttempts(defaultValue int, override *int) int {
	if override != nil {
		return *override
	}
	if defaultValue <= 0 {
		return 0
	}
	return defaultValue
}

func isExact(answer, correct string) bool {
	return strings.EqualFold(strings.TrimSpace(answer), strings.TrimSpace(correct))
}
