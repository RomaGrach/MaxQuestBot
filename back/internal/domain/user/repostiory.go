package user

import "context"

type Repository interface {
	List(ctx context.Context) ([]User, error)
	GetByID(ctx context.Context, id int64) (User, error)
	GetByMaxUserID(ctx context.Context, maxUserID string) (User, error)
	Create(ctx context.Context, u User) (User, error)
	Update(ctx context.Context, u User) (User, error)
	UpdateComment(ctx context.Context, id int64, comment string) (User, error)
}
