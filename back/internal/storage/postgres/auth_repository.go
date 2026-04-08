package postgres

import (
	"context"

	"github.com/RomaGrach/quest-bot-backend/internal/domain/auth"
	"github.com/RomaGrach/quest-bot-backend/internal/domain/common"
)

type AuthRepository struct {
	db *DB
}

func NewAuthRepository(db *DB) *AuthRepository {
	return &AuthRepository{db: db}
}

func (r *AuthRepository) GetByID(_ context.Context, id int64) (auth.Admin, error) {
	r.db.mu.RLock()
	defer r.db.mu.RUnlock()

	admin, ok := r.db.admins[id]
	if !ok {
		return auth.Admin{}, common.ErrNotFound
	}
	return admin, nil
}

func (r *AuthRepository) GetByUsername(_ context.Context, username string) (auth.Admin, error) {
	r.db.mu.RLock()
	defer r.db.mu.RUnlock()

	id, ok := r.db.adminByLogin[username]
	if !ok {
		return auth.Admin{}, common.ErrNotFound
	}
	admin, ok := r.db.admins[id]
	if !ok {
		return auth.Admin{}, common.ErrNotFound
	}
	return admin, nil
}

func (r *AuthRepository) Upsert(_ context.Context, admin auth.Admin) (auth.Admin, error) {
	r.db.mu.Lock()
	defer r.db.mu.Unlock()

	if existingID, ok := r.db.adminByLogin[admin.Username]; ok {
		admin.ID = existingID
		r.db.admins[existingID] = admin
		return admin, nil
	}
	r.db.nextAdminID++
	admin.ID = r.db.nextAdminID
	r.db.admins[admin.ID] = admin
	r.db.adminByLogin[admin.Username] = admin.ID
	return admin, nil
}
