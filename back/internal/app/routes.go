package app

import (
	"net/http"

	httptransport "github.com/RomaGrach/quest-bot-backend/internal/transport/http"
	adminhandlers "github.com/RomaGrach/quest-bot-backend/internal/transport/http/admin"
	bothandlers "github.com/RomaGrach/quest-bot-backend/internal/transport/http/bot"
)

func BuildRouter(c *Container) http.Handler {
	return httptransport.NewRouter(httptransport.RouterDeps{
		Logger:       c.Logger,
		TokenManager: c.TokenManager,

		AdminPing: adminhandlers.Ping,

		AdminLogin:          c.AdminAuthHandler.Login,
		AdminQuestList:      c.AdminQuestHandler.List,
		AdminQuestCreate:    c.AdminQuestHandler.Create,
		AdminQuestUpdate:    c.AdminQuestHandler.Update,
		AdminQuestDelete:    c.AdminQuestHandler.Delete,
		AdminQuestionList:   c.AdminQuestionHandler.ListByQuest,
		AdminQuestionCreate: c.AdminQuestionHandler.Create,
		AdminQuestionUpdate: c.AdminQuestionHandler.Update,
		AdminQuestionDelete: c.AdminQuestionHandler.Delete,
		AdminUserList:       c.AdminUserHandler.List,
		AdminUserAttempts:   c.AdminUserHandler.AttemptsByUser,
		AdminUserComment:    c.AdminUserHandler.UpdateComment,
		AdminStats:          c.AdminStatsHandler.Get,
		AdminStatsExport:    c.AdminStatsHandler.ExportCSV,
		AdminGiftMark:       c.AdminGiftHandler.MarkIssued,

		BotPing:       bothandlers.Ping,
		BotRegister:   c.BotRegistrationHandler.Register,
		BotQuestList:  c.BotQuestHandler.List,
		BotQuestStart: c.BotQuestHandler.Start,
		BotQuestState: c.BotQuestHandler.State,
		BotAnswer:     c.BotAnswerHandler.Submit,
		BotHint:       c.BotAnswerHandler.Hint,
		BotWebhook:    c.BotWebhookHandler.Handle,
	})
}
