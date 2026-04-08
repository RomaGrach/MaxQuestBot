package quest

import "context"

type Repository interface {
	List(ctx context.Context) ([]Quest, error)
	ListPublished(ctx context.Context) ([]Quest, error)
	GetByID(ctx context.Context, id int64) (Quest, error)
	Create(ctx context.Context, q Quest) (Quest, error)
	Update(ctx context.Context, q Quest) (Quest, error)
	Delete(ctx context.Context, id int64) error
}
