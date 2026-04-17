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

func (r *AuthRepository) GetByID(ctx context.Context, id int64) (auth.Admin, error) {
	row := r.db.sql.QueryRowContext(ctx, `
			SELECT id, username, password_hash, role
			FROM admins
			WHERE id = $1
		`, id)
	admin, err := scanAdmin(row)
	if err != nil {
		return auth.Admin{}, mapSQLError(err)
	}
	return admin, nil
}

func (r *AuthRepository) GetByUsername(ctx context.Context, username string) (auth.Admin, error) {
	row := r.db.sql.QueryRowContext(ctx, `
			SELECT id, username, password_hash, role
			FROM admins
			WHERE username = $1
		`, username)
	admin, err := scanAdmin(row)
	if err != nil {
		return auth.Admin{}, mapSQLError(err)
	}
	return admin, nil
}

func (r *AuthRepository) Upsert(ctx context.Context, admin auth.Admin) (auth.Admin, error) {
	row := r.db.sql.QueryRowContext(ctx, `
			INSERT INTO admins (username, password_hash, role)
			VALUES ($1, $2, $3)
			ON CONFLICT (username) DO UPDATE
			SET password_hash = EXCLUDED.password_hash,
				role = EXCLUDED.role
			RETURNING id, username, password_hash, role
		`, admin.Username, admin.PasswordHash, string(admin.Role))
	return scanAdmin(row)
}

type adminScanner interface {
	Scan(dest ...any) error
}

func scanAdmin(row adminScanner) (auth.Admin, error) {
	var admin auth.Admin
	var role string
	err := row.Scan(
		&admin.ID,
		&admin.Username,
		&admin.PasswordHash,
		&role,
	)
	if err != nil {
		return auth.Admin{}, err
	}
	admin.Role = common.Role(role)
	return admin, nil
}
