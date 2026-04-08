package app

import (
	"fmt"
	"net/http"
	"time"

	"github.com/RomaGrach/quest-bot-backend/internal/config"
)

type App struct {
	server *http.Server
}

func New(cfg config.Config) *App {
	container := NewContainer(cfg)
	router := BuildRouter(container)

	server := &http.Server{
		Addr:              ":" + cfg.Port,
		Handler:           router,
		ReadHeaderTimeout: 5 * time.Second,
	}

	return &App{
		server: server,
	}
}

func (a *App) Run() error {
	fmt.Println("server started on", a.server.Addr)
	return a.server.ListenAndServe()
}
