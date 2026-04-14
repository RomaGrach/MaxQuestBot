package auth

import "context"

type Repository interface {
	GetByID(ctx context.Context, id int64) (Admin, error)
	GetByUsername(ctx context.Context, username string) (Admin, error)
	Upsert(ctx context.Context, admin Admin) (Admin, error)
}
