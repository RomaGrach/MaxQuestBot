package max

import "context"

type Client interface {
	SendText(ctx context.Context, chatID, text string) error
}

type NopClient struct{}

func (NopClient) SendText(_ context.Context, _ string, _ string) error {
	return nil
}
