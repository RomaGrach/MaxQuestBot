package postgres

import (
	"context"
	"database/sql"
	"errors"

	"github.com/RomaGrach/quest-bot-backend/internal/domain/common"
	"github.com/RomaGrach/quest-bot-backend/internal/domain/user"
)

type UserRepository struct {
	db *DB
}

func NewUserRepository(db *DB) *UserRepository {
	return &UserRepository{db: db}
}

func (r *UserRepository) List(ctx context.Context) ([]user.User, error) {
	rows, err := r.db.sql.QueryContext(ctx, `
			SELECT id, max_user_id, phone, consent, comment, registered_at
			FROM users
			ORDER BY id
		`)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	items := make([]user.User, 0)
	for rows.Next() {
		u, err := scanUser(rows)
		if err != nil {
			return nil, err
		}
		items = append(items, u)
	}
	return items, rows.Err()
}

func (r *UserRepository) GetByID(ctx context.Context, id int64) (user.User, error) {
	row := r.db.sql.QueryRowContext(ctx, `
			SELECT id, max_user_id, phone, consent, comment, registered_at
			FROM users
			WHERE id = $1
		`, id)
	u, err := scanUser(row)
	if err != nil {
		return user.User{}, mapSQLError(err)
	}
	return u, nil
}

func (r *UserRepository) GetByMaxUserID(ctx context.Context, maxUserID string) (user.User, error) {
	row := r.db.sql.QueryRowContext(ctx, `
			SELECT id, max_user_id, phone, consent, comment, registered_at
			FROM users
			WHERE max_user_id = $1
		`, maxUserID)
	u, err := scanUser(row)
	if err != nil {
		return user.User{}, mapSQLError(err)
	}
	return u, nil
}

func (r *UserRepository) Create(ctx context.Context, u user.User) (user.User, error) {
	if !u.RegisteredAt.IsZero() {
		row := r.db.sql.QueryRowContext(ctx, `
				INSERT INTO users (max_user_id, phone, consent, comment, registered_at)
				VALUES ($1, $2, $3, $4, $5)
				ON CONFLICT (max_user_id) DO NOTHING
				RETURNING id, max_user_id, phone, consent, comment, registered_at
			`, u.MaxUserID, u.Phone, u.Consent, u.Comment, u.RegisteredAt)
		created, err := scanUser(row)
		if errors.Is(err, sql.ErrNoRows) {
			return user.User{}, common.ErrConflict
		}
		return created, err
	}

	row := r.db.sql.QueryRowContext(ctx, `
			INSERT INTO users (max_user_id, phone, consent, comment)
			VALUES ($1, $2, $3, $4)
			ON CONFLICT (max_user_id) DO NOTHING
			RETURNING id, max_user_id, phone, consent, comment, registered_at
		`, u.MaxUserID, u.Phone, u.Consent, u.Comment)
	created, err := scanUser(row)
	if errors.Is(err, sql.ErrNoRows) {
		return user.User{}, common.ErrConflict
	}
	return created, err
}

func (r *UserRepository) Update(ctx context.Context, u user.User) (user.User, error) {
	row := r.db.sql.QueryRowContext(ctx, `
			UPDATE users
			SET max_user_id = $2, phone = $3, consent = $4, comment = $5
			WHERE id = $1
			RETURNING id, max_user_id, phone, consent, comment, registered_at
		`, u.ID, u.MaxUserID, u.Phone, u.Consent, u.Comment)
	updated, err := scanUser(row)
	if err != nil {
		return user.User{}, mapSQLError(err)
	}
	return updated, nil
}

func (r *UserRepository) UpdateComment(ctx context.Context, id int64, comment string) (user.User, error) {
	row := r.db.sql.QueryRowContext(ctx, `
			UPDATE users
			SET comment = $2
			WHERE id = $1
			RETURNING id, max_user_id, phone, consent, comment, registered_at
		`, id, comment)
	updated, err := scanUser(row)
	if err != nil {
		return user.User{}, mapSQLError(err)
	}
	return updated, nil
}

type userScanner interface {
	Scan(dest ...any) error
}

func scanUser(row userScanner) (user.User, error) {
	var u user.User
	err := row.Scan(
		&u.ID,
		&u.MaxUserID,
		&u.Phone,
		&u.Consent,
		&u.Comment,
		&u.RegisteredAt,
	)
	if err != nil {
		return user.User{}, err
	}
	return u, nil
}
