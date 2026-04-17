package app

import (
	"context"
	"io"
	"log/slog"

	"github.com/RomaGrach/quest-bot-backend/internal/config"
	"github.com/RomaGrach/quest-bot-backend/internal/domain/auth"
	"github.com/RomaGrach/quest-bot-backend/internal/domain/common"
	"github.com/RomaGrach/quest-bot-backend/internal/domain/question"
	"github.com/RomaGrach/quest-bot-backend/internal/observability"
	"github.com/RomaGrach/quest-bot-backend/internal/security"
	"github.com/RomaGrach/quest-bot-backend/internal/storage/postgres"
	adminhandlers "github.com/RomaGrach/quest-bot-backend/internal/transport/http/admin"
	bothandlers "github.com/RomaGrach/quest-bot-backend/internal/transport/http/bot"
	maxtransport "github.com/RomaGrach/quest-bot-backend/internal/transport/max"
	adminuc "github.com/RomaGrach/quest-bot-backend/internal/usecase/admin"
	botuc "github.com/RomaGrach/quest-bot-backend/internal/usecase/bot"
)

type Container struct {
	Logger       *slog.Logger
	TokenManager *security.TokenManager
	Closer       io.Closer

	AdminAuthHandler     *adminhandlers.AuthHandler
	AdminQuestHandler    *adminhandlers.QuestHandler
	AdminQuestionHandler *adminhandlers.QuestionHandler
	AdminUserHandler     *adminhandlers.UserHandler
	AdminStatsHandler    *adminhandlers.StatsHandler
	AdminGiftHandler     *adminhandlers.GiftHandler

	BotRegistrationHandler *bothandlers.RegistrationHandler
	BotQuestHandler        *bothandlers.QuestHandler
	BotAnswerHandler       *bothandlers.AnswerHandler
	BotWebhookHandler      *bothandlers.WebhookHandler
}

func NewContainer(ctx context.Context, cfg config.Config) (*Container, error) {
	logger := observability.NewLogger(slog.LevelInfo)
	hasher := security.NewSHA256Hasher(cfg.Auth.PasswordSalt)
	tokenManager := security.NewTokenManager(cfg.Auth.TokenSecret, cfg.Auth.TokenTTL)

	db, err := postgres.Open(ctx, cfg.DatabaseURL)
	if err != nil {
		return nil, err
	}

	questRepo := postgres.NewQuestRepository(db)
	questionRepo := postgres.NewQuestionRepository(db)
	userRepo := postgres.NewUserRepository(db)
	attemptRepo := postgres.NewAttemptRepository(db)
	authRepo := postgres.NewAuthRepository(db)

	_, _ = authRepo.Upsert(ctx, auth.Admin{
		Username:     cfg.Auth.AdminUsername,
		PasswordHash: hasher.Hash(cfg.Auth.AdminPassword),
		Role:         common.RoleAdmin,
	})

	if cfg.Auth.OperatorUsername != "" {
		_, _ = authRepo.Upsert(ctx, auth.Admin{
			Username:     cfg.Auth.OperatorUsername,
			PasswordHash: hasher.Hash(cfg.Auth.OperatorPassword),
			Role:         common.RoleOperator,
		})
	}

	questMatcher := question.SimpleMatcher{}

	adminAuthUC := adminuc.NewAuthUseCase(authRepo, hasher, tokenManager)
	adminQuestUC := adminuc.NewQuestUseCase(questRepo)
	adminQuestionUC := adminuc.NewQuestionUseCase(questionRepo)
	adminUserUC := adminuc.NewUserUseCase(userRepo, attemptRepo, questRepo)
	adminStatsUC := adminuc.NewStatsUseCase(userRepo, attemptRepo)
	adminGiftUC := adminuc.NewGiftUseCase(attemptRepo)

	botRegistrationUC := botuc.NewRegistrationUseCase(userRepo)
	botQuestListUC := botuc.NewQuestListUseCase(userRepo, questRepo)
	botStartQuestUC := botuc.NewStartQuestUseCase(userRepo, questRepo, questionRepo, attemptRepo)
	botAnswerUC := botuc.NewAnswerUseCase(userRepo, questRepo, questionRepo, attemptRepo, questMatcher)
	botHintUC := botuc.NewHintUseCase(userRepo, attemptRepo, questionRepo)
	botStateUC := botuc.NewFinishUseCase(userRepo, questRepo, attemptRepo, questionRepo)

	return &Container{
		Logger:       logger,
		TokenManager: tokenManager,
		Closer:       db,

		AdminAuthHandler:     adminhandlers.NewAuthHandler(adminAuthUC),
		AdminQuestHandler:    adminhandlers.NewQuestHandler(adminQuestUC),
		AdminQuestionHandler: adminhandlers.NewQuestionHandler(adminQuestionUC),
		AdminUserHandler:     adminhandlers.NewUserHandler(adminUserUC),
		AdminStatsHandler:    adminhandlers.NewStatsHandler(adminStatsUC),
		AdminGiftHandler:     adminhandlers.NewGiftHandler(adminGiftUC),

		BotRegistrationHandler: bothandlers.NewRegistrationHandler(botRegistrationUC),
		BotQuestHandler:        bothandlers.NewQuestHandler(botQuestListUC, botStartQuestUC, botStateUC),
		BotAnswerHandler:       bothandlers.NewAnswerHandler(botAnswerUC, botHintUC),
		BotWebhookHandler:      bothandlers.NewWebhookHandler(maxtransport.NewSigner(cfg.Max.WebhookSecret)),
	}, nil
}