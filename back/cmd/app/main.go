package main

import (
	"log"

	"github.com/RomaGrach/quest-bot-backend/internal/app"
	"github.com/RomaGrach/quest-bot-backend/internal/config"
)

func main() {
	cfg := config.MustLoad()

	application, err := app.New(cfg)
	if err != nil {
		log.Fatal(err)
	}
	defer func() {
		if err := application.Close(); err != nil {
			log.Println("close app:", err)
		}
	}()

	if err := application.Run(); err != nil {
		log.Fatal(err)
	}
}
