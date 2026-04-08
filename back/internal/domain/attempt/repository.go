package attempt

import "context"

type Repository interface {
	List(ctx context.Context) ([]Attempt, error)
	ListByUserID(ctx context.Context, userID int64) ([]Attempt, error)
	GetByID(ctx context.Context, id int64) (Attempt, error)
	GetByUserAndQuest(ctx context.Context, userID, questID int64) (Attempt, error)
	GetActiveByUserID(ctx context.Context, userID int64) (Attempt, error)
	Create(ctx context.Context, a Attempt) (Attempt, error)
	Update(ctx context.Context, a Attempt) (Attempt, error)
}
