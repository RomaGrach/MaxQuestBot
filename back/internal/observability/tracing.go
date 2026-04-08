package observability

import "context"

type Tracer struct{}

func NewTracer() *Tracer {
	return &Tracer{}
}

func (t *Tracer) Start(ctx context.Context, _ string) (context.Context, func()) {
	return ctx, func() {}
}
