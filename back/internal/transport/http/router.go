package httptransport

import (
	"encoding/json"
	"log/slog"
	"net/http"

	"github.com/RomaGrach/quest-bot-backend/internal/security"
	"github.com/RomaGrach/quest-bot-backend/internal/transport/http/middleware"
)

type RouterDeps struct {
	Logger       *slog.Logger
	TokenManager *security.TokenManager

	AdminPing           http.HandlerFunc
	AdminLogin          http.HandlerFunc
	AdminQuestList      http.HandlerFunc
	AdminQuestCreate    http.HandlerFunc
	AdminQuestUpdate    http.HandlerFunc
	AdminQuestDelete    http.HandlerFunc
	AdminQuestionList   http.HandlerFunc
	AdminQuestionCreate http.HandlerFunc
	AdminQuestionUpdate http.HandlerFunc
	AdminQuestionDelete http.HandlerFunc
	AdminUserList       http.HandlerFunc
	AdminUserAttempts   http.HandlerFunc
	AdminUserComment    http.HandlerFunc
	AdminStats          http.HandlerFunc
	AdminStatsExport    http.HandlerFunc
	AdminGiftMark       http.HandlerFunc

	BotPing       http.HandlerFunc
	BotRegister   http.HandlerFunc
	BotQuestList  http.HandlerFunc
	BotQuestStart http.HandlerFunc
	BotQuestState http.HandlerFunc
	BotAnswer     http.HandlerFunc
	BotHint       http.HandlerFunc
	BotWebhook    http.HandlerFunc
}

func NewRouter(deps RouterDeps) http.Handler {
	mux := http.NewServeMux()

	// Public.
	mux.HandleFunc("GET /health", healthHandler)
	mux.HandleFunc("GET /admin/ping", deps.AdminPing)
	mux.HandleFunc("GET /bot/ping", deps.BotPing)
	mux.HandleFunc("POST /admin/auth/login", deps.AdminLogin)
	mux.HandleFunc("POST /bot/register", deps.BotRegister)
	mux.HandleFunc("GET /bot/quests", deps.BotQuestList)
	mux.HandleFunc("POST /bot/quests/{quest_id}/start", deps.BotQuestStart)
	mux.HandleFunc("GET /bot/quests/{quest_id}/state", deps.BotQuestState)
	mux.HandleFunc("POST /bot/quests/{quest_id}/answer", deps.BotAnswer)
	mux.HandleFunc("POST /bot/quests/{quest_id}/hint", deps.BotHint)
	mux.HandleFunc("POST /bot/webhook", deps.BotWebhook)

	// Protected admin endpoints.
	adminOnly := middleware.RequireAuth(deps.TokenManager, security.RoleAdmin)
	staff := middleware.RequireAuth(deps.TokenManager, security.RoleAdmin, security.RoleOperator)

	mux.Handle("GET /admin/quests", adminOnly(http.HandlerFunc(deps.AdminQuestList)))
	mux.Handle("POST /admin/quests", adminOnly(http.HandlerFunc(deps.AdminQuestCreate)))
	mux.Handle("PUT /admin/quests/{quest_id}", adminOnly(http.HandlerFunc(deps.AdminQuestUpdate)))
	mux.Handle("DELETE /admin/quests/{quest_id}", adminOnly(http.HandlerFunc(deps.AdminQuestDelete)))

	mux.Handle("GET /admin/quests/{quest_id}/questions", adminOnly(http.HandlerFunc(deps.AdminQuestionList)))
	mux.Handle("POST /admin/quests/{quest_id}/questions", adminOnly(http.HandlerFunc(deps.AdminQuestionCreate)))
	mux.Handle("PUT /admin/quests/{quest_id}/questions/{question_id}", adminOnly(http.HandlerFunc(deps.AdminQuestionUpdate)))
	mux.Handle("DELETE /admin/quests/{quest_id}/questions/{question_id}", adminOnly(http.HandlerFunc(deps.AdminQuestionDelete)))

	mux.Handle("GET /admin/users", staff(http.HandlerFunc(deps.AdminUserList)))
	mux.Handle("GET /admin/users/{user_id}/attempts", staff(http.HandlerFunc(deps.AdminUserAttempts)))
	mux.Handle("PATCH /admin/users/{user_id}/comment", staff(http.HandlerFunc(deps.AdminUserComment)))
	mux.Handle("GET /admin/stats", staff(http.HandlerFunc(deps.AdminStats)))
	mux.Handle("GET /admin/stats/export.csv", staff(http.HandlerFunc(deps.AdminStatsExport)))
	mux.Handle("POST /admin/attempts/{attempt_id}/gift", staff(http.HandlerFunc(deps.AdminGiftMark)))

	return middleware.Recovery(middleware.RequestID(middleware.Logging(deps.Logger)(mux)))
}

func healthHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		w.WriteHeader(http.StatusMethodNotAllowed)
		return
	}

	writeJSON(w, http.StatusOK, map[string]string{
		"status": "ok",
	})
}

func writeJSON(w http.ResponseWriter, status int, data any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(data)
}
