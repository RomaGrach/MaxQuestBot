package postgres

import (
	"context"
	"sort"
	"time"

	"github.com/RomaGrach/quest-bot-backend/internal/domain/common"
	"github.com/RomaGrach/quest-bot-backend/internal/domain/user"
)

type UserRepository struct {
	db *DB
}

func NewUserRepository(db *DB) *UserRepository {
	return &UserRepository{db: db}
}

func (r *UserRepository) List(_ context.Context) ([]user.User, error) {
	r.db.mu.RLock()
	defer r.db.mu.RUnlock()

	out := make([]user.User, 0, len(r.db.users))
	for _, u := range r.db.users {
		out = append(out, u)
	}
	sort.Slice(out, func(i, j int) bool { return out[i].ID < out[j].ID })
	return out, nil
}

func (r *UserRepository) GetByID(_ context.Context, id int64) (user.User, error) {
	r.db.mu.RLock()
	defer r.db.mu.RUnlock()

	u, ok := r.db.users[id]
	if !ok {
		return user.User{}, common.ErrNotFound
	}
	return u, nil
}

func (r *UserRepository) GetByMaxUserID(_ context.Context, maxUserID string) (user.User, error) {
	r.db.mu.RLock()
	defer r.db.mu.RUnlock()

	id, ok := r.db.usersByMaxID[maxUserID]
	if !ok {
		return user.User{}, common.ErrNotFound
	}
	u, ok := r.db.users[id]
	if !ok {
		return user.User{}, common.ErrNotFound
	}
	return u, nil
}

func (r *UserRepository) Create(_ context.Context, u user.User) (user.User, error) {
	r.db.mu.Lock()
	defer r.db.mu.Unlock()

	if _, exists := r.db.usersByMaxID[u.MaxUserID]; exists {
		return user.User{}, common.ErrConflict
	}
	r.db.nextUserID++
	u.ID = r.db.nextUserID
	if u.RegisteredAt.IsZero() {
		u.RegisteredAt = time.Now()
	}
	r.db.users[u.ID] = u
	r.db.usersByMaxID[u.MaxUserID] = u.ID
	return u, nil
}

func (r *UserRepository) Update(_ context.Context, u user.User) (user.User, error) {
	r.db.mu.Lock()
	defer r.db.mu.Unlock()

	existing, ok := r.db.users[u.ID]
	if !ok {
		return user.User{}, common.ErrNotFound
	}
	if existing.MaxUserID != u.MaxUserID {
		delete(r.db.usersByMaxID, existing.MaxUserID)
		r.db.usersByMaxID[u.MaxUserID] = u.ID
	}
	if u.RegisteredAt.IsZero() {
		u.RegisteredAt = existing.RegisteredAt
	}
	r.db.users[u.ID] = u
	return u, nil
}

func (r *UserRepository) UpdateComment(ctx context.Context, id int64, comment string) (user.User, error) {
	u, err := r.GetByID(ctx, id)
	if err != nil {
		return user.User{}, err
	}
	u.Comment = comment
	return r.Update(ctx, u)
}
