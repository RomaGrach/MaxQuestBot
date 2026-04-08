package main

import (
	"log"

	"github.com/RomaGrach/quest-bot-backend/internal/app"
	"github.com/RomaGrach/quest-bot-backend/internal/config"
)

func main() {
	cfg := config.MustLoad()

	application := app.New(cfg)

	if err := application.Run(); err != nil {
		log.Fatal(err)
	}
}
