package question

import "context"

type Repository interface {
	ListByQuestID(ctx context.Context, questID int64) ([]Question, error)
	GetByQuestAndOrder(ctx context.Context, questID int64, order int) (Question, error)
	Create(ctx context.Context, q Question) (Question, error)
	Update(ctx context.Context, q Question) (Question, error)
	Delete(ctx context.Context, id int64) error
}
