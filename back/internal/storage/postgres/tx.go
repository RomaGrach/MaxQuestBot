package postgres

import "context"

type Transactor struct{}

func NewTransactor() *Transactor {
	return &Transactor{}
}

func (t *Transactor) WithinTransaction(ctx context.Context, fn func(context.Context) error) error {
	return fn(ctx)
}
