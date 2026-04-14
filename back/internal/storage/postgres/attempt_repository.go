package postgres

import (
	"context"
	"sort"
	"time"

	"github.com/RomaGrach/quest-bot-backend/internal/domain/attempt"
	"github.com/RomaGrach/quest-bot-backend/internal/domain/common"
)

type AttemptRepository struct {
	db *DB
}

func NewAttemptRepository(db *DB) *AttemptRepository {
	return &AttemptRepository{db: db}
}

func (r *AttemptRepository) List(_ context.Context) ([]attempt.Attempt, error) {
	r.db.mu.RLock()
	defer r.db.mu.RUnlock()

	out := make([]attempt.Attempt, 0, len(r.db.attempts))
	for _, a := range r.db.attempts {
		out = append(out, cloneAttempt(a))
	}
	sort.Slice(out, func(i, j int) bool { return out[i].ID < out[j].ID })
	return out, nil
}

func (r *AttemptRepository) ListByUserID(_ context.Context, userID int64) ([]attempt.Attempt, error) {
	r.db.mu.RLock()
	defer r.db.mu.RUnlock()

	out := make([]attempt.Attempt, 0)
	for _, a := range r.db.attempts {
		if a.UserID == userID {
			out = append(out, cloneAttempt(a))
		}
	}
	sort.Slice(out, func(i, j int) bool { return out[i].StartedAt.Before(out[j].StartedAt) })
	return out, nil
}

func (r *AttemptRepository) GetByID(_ context.Context, id int64) (attempt.Attempt, error) {
	r.db.mu.RLock()
	defer r.db.mu.RUnlock()

	a, ok := r.db.attempts[id]
	if !ok {
		return attempt.Attempt{}, common.ErrNotFound
	}
	return cloneAttempt(a), nil
}

func (r *AttemptRepository) GetByUserAndQuest(_ context.Context, userID, questID int64) (attempt.Attempt, error) {
	r.db.mu.RLock()
	defer r.db.mu.RUnlock()

	var latest attempt.Attempt
	found := false
	for _, a := range r.db.attempts {
		if a.UserID != userID || a.QuestID != questID {
			continue
		}
		if !found || a.StartedAt.After(latest.StartedAt) {
			latest = a
			found = true
		}
	}
	if !found {
		return attempt.Attempt{}, common.ErrNotFound
	}
	return cloneAttempt(latest), nil
}

func (r *AttemptRepository) GetActiveByUserID(_ context.Context, userID int64) (attempt.Attempt, error) {
	r.db.mu.RLock()
	defer r.db.mu.RUnlock()

	for _, a := range r.db.attempts {
		if a.UserID == userID && a.Status == attempt.StatusInProgress {
			return cloneAttempt(a), nil
		}
	}
	return attempt.Attempt{}, common.ErrNotFound
}

func (r *AttemptRepository) Create(_ context.Context, a attempt.Attempt) (attempt.Attempt, error) {
	r.db.mu.Lock()
	defer r.db.mu.Unlock()

	r.db.nextAttemptID++
	a.ID = r.db.nextAttemptID
	if a.StartedAt.IsZero() {
		a.StartedAt = time.Now()
	}
	if a.AttemptsByQuestion == nil {
		a.AttemptsByQuestion = make(map[int]int)
	}
	r.db.attempts[a.ID] = cloneAttempt(a)
	return cloneAttempt(a), nil
}

func (r *AttemptRepository) Update(_ context.Context, a attempt.Attempt) (attempt.Attempt, error) {
	r.db.mu.Lock()
	defer r.db.mu.Unlock()

	if _, ok := r.db.attempts[a.ID]; !ok {
		return attempt.Attempt{}, common.ErrNotFound
	}
	if a.AttemptsByQuestion == nil {
		a.AttemptsByQuestion = make(map[int]int)
	}
	r.db.attempts[a.ID] = cloneAttempt(a)
	return cloneAttempt(a), nil
}

func cloneAttempt(a attempt.Attempt) attempt.Attempt {
	if a.AttemptsByQuestion == nil {
		a.AttemptsByQuestion = make(map[int]int)
		return a
	}
	cp := make(map[int]int, len(a.AttemptsByQuestion))
	for k, v := range a.AttemptsByQuestion {
		cp[k] = v
	}
	a.AttemptsByQuestion = cp
	return a
}
