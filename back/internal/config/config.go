package config

import (
	"os"
	"time"
)

type Config struct {
	Port        string
	DatabaseURL string
	Auth        AuthConfig
	Max         MaxConfig
}

type AuthConfig struct {
	TokenSecret      string
	TokenTTL         time.Duration
	PasswordSalt     string
	AdminUsername    string
	AdminPassword    string
	OperatorUsername string
	OperatorPassword string
}

type MaxConfig struct {
	WebhookSecret string
}

func MustLoad() Config {
	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}

	tokenTTL, err := time.ParseDuration(getEnv("AUTH_TOKEN_TTL", "24h"))
	if err != nil {
		tokenTTL = 24 * time.Hour
	}

	return Config{
		Port:        port,
		DatabaseURL: os.Getenv("DATABASE_URL"),
		Auth: AuthConfig{
			TokenSecret:      getEnv("AUTH_TOKEN_SECRET", "dev-secret"),
			TokenTTL:         tokenTTL,
			PasswordSalt:     getEnv("AUTH_PASSWORD_SALT", "dev-salt"),
			AdminUsername:    getEnv("AUTH_ADMIN_USERNAME", "admin"),
			AdminPassword:    getEnv("AUTH_ADMIN_PASSWORD", "admin123"),
			OperatorUsername: getEnv("AUTH_OPERATOR_USERNAME", "operator"),
			OperatorPassword: getEnv("AUTH_OPERATOR_PASSWORD", "operator"),
		},
		Max: MaxConfig{
			WebhookSecret: getEnv("MAX_WEBHOOK_SECRET", "max-dev-secret"),
		},
	}
}

func getEnv(key, fallback string) string {
	value := os.Getenv(key)
	if value == "" {
		return fallback
	}
	return value
}
