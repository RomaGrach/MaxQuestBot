package postgres

import (
	"context"
	"sort"
	"time"

	"github.com/RomaGrach/quest-bot-backend/internal/domain/common"
	"github.com/RomaGrach/quest-bot-backend/internal/domain/quest"
)

type QuestRepository struct {
	db *DB
}

func NewQuestRepository(db *DB) *QuestRepository {
	return &QuestRepository{db: db}
}

func (r *QuestRepository) List(_ context.Context) ([]quest.Quest, error) {
	r.db.mu.RLock()
	defer r.db.mu.RUnlock()

	out := make([]quest.Quest, 0, len(r.db.quests))
	for _, q := range r.db.quests {
		out = append(out, q)
	}
	sort.Slice(out, func(i, j int) bool { return out[i].ID < out[j].ID })
	return out, nil
}

func (r *QuestRepository) ListPublished(ctx context.Context) ([]quest.Quest, error) {
	all, err := r.List(ctx)
	if err != nil {
		return nil, err
	}
	out := make([]quest.Quest, 0, len(all))
	for _, q := range all {
		if q.Status == quest.StatusPublished {
			out = append(out, q)
		}
	}
	return out, nil
}

func (r *QuestRepository) GetByID(_ context.Context, id int64) (quest.Quest, error) {
	r.db.mu.RLock()
	defer r.db.mu.RUnlock()

	q, ok := r.db.quests[id]
	if !ok {
		return quest.Quest{}, common.ErrNotFound
	}
	return q, nil
}

func (r *QuestRepository) Create(_ context.Context, q quest.Quest) (quest.Quest, error) {
	r.db.mu.Lock()
	defer r.db.mu.Unlock()

	r.db.nextQuestID++
	q.ID = r.db.nextQuestID
	now := time.Now()
	q.CreatedAt = now
	q.UpdatedAt = now
	r.db.quests[q.ID] = q
	return q, nil
}

func (r *QuestRepository) Update(_ context.Context, q quest.Quest) (quest.Quest, error) {
	r.db.mu.Lock()
	defer r.db.mu.Unlock()

	existing, ok := r.db.quests[q.ID]
	if !ok {
		return quest.Quest{}, common.ErrNotFound
	}
	q.CreatedAt = existing.CreatedAt
	q.UpdatedAt = time.Now()
	r.db.quests[q.ID] = q
	return q, nil
}

func (r *QuestRepository) Delete(_ context.Context, id int64) error {
	r.db.mu.Lock()
	defer r.db.mu.Unlock()

	if _, ok := r.db.quests[id]; !ok {
		return common.ErrNotFound
	}
	delete(r.db.quests, id)
	return nil
}
