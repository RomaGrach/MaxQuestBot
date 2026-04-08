package postgres

import (
	"context"
	"sort"

	"github.com/RomaGrach/quest-bot-backend/internal/domain/common"
	"github.com/RomaGrach/quest-bot-backend/internal/domain/question"
)

type QuestionRepository struct {
	db *DB
}

func NewQuestionRepository(db *DB) *QuestionRepository {
	return &QuestionRepository{db: db}
}

func (r *QuestionRepository) ListByQuestID(_ context.Context, questID int64) ([]question.Question, error) {
	r.db.mu.RLock()
	defer r.db.mu.RUnlock()

	out := make([]question.Question, 0)
	for _, q := range r.db.questions {
		if q.QuestID == questID {
			out = append(out, q)
		}
	}
	sort.Slice(out, func(i, j int) bool { return out[i].Order < out[j].Order })
	return out, nil
}

func (r *QuestionRepository) GetByQuestAndOrder(_ context.Context, questID int64, order int) (question.Question, error) {
	r.db.mu.RLock()
	defer r.db.mu.RUnlock()

	for _, q := range r.db.questions {
		if q.QuestID == questID && q.Order == order {
			return q, nil
		}
	}
	return question.Question{}, common.ErrNotFound
}

func (r *QuestionRepository) Create(_ context.Context, q question.Question) (question.Question, error) {
	r.db.mu.Lock()
	defer r.db.mu.Unlock()

	r.db.nextQuestionID++
	q.ID = r.db.nextQuestionID
	r.db.questions[q.ID] = q
	return q, nil
}

func (r *QuestionRepository) Update(_ context.Context, q question.Question) (question.Question, error) {
	r.db.mu.Lock()
	defer r.db.mu.Unlock()

	if _, ok := r.db.questions[q.ID]; !ok {
		return question.Question{}, common.ErrNotFound
	}
	r.db.questions[q.ID] = q
	return q, nil
}

func (r *QuestionRepository) Delete(_ context.Context, id int64) error {
	r.db.mu.Lock()
	defer r.db.mu.Unlock()

	if _, ok := r.db.questions[id]; !ok {
		return common.ErrNotFound
	}
	delete(r.db.questions, id)
	return nil
}
