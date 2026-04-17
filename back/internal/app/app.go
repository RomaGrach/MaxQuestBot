package app

import (
	"context"
	"fmt"
	"net/http"
	"time"

	"github.com/RomaGrach/quest-bot-backend/internal/config"
)

type App struct {
	server *http.Server
	closers []func() error
}

func New(cfg config.Config) (*App, error) {
	container, err := NewContainer(context.Background(), cfg)
	if err != nil {
		return nil, err
	}
	router := BuildRouter(container)

	server := &http.Server{
		Addr:              ":" + cfg.Port,
		Handler:           router,
		ReadHeaderTimeout: 5 * time.Second,
	}

	app := &App{
		server: server,
	}

	if container.Closer != nil {
		app.closers = append(app.closers, container.Closer.Close)
	}

	return app, nil
}

func (a *App) Run() error {
	fmt.Println("server started on", a.server.Addr)
	return a.server.ListenAndServe()
}

func (a *App) Close() error {
	var firstErr error
	for _, closeFn := range a.closers {
		if err := closeFn(); err != nil && firstErr == nil {
			firstErr = err
		}
	}
	return firstErr
}