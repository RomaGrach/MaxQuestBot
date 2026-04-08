package bot

import (
	"net/http"

	"github.com/RomaGrach/quest-bot-backend/internal/transport/http/dto"
	botuc "github.com/RomaGrach/quest-bot-backend/internal/usecase/bot"
)

type QuestHandler struct {
	listUC  *botuc.QuestListUseCase
	startUC *botuc.StartQuestUseCase
	stateUC *botuc.FinishUseCase
}

func NewQuestHandler(
	listUC *botuc.QuestListUseCase,
	startUC *botuc.StartQuestUseCase,
	stateUC *botuc.FinishUseCase,
) *QuestHandler {
	return &QuestHandler{
		listUC:  listUC,
		startUC: startUC,
		stateUC: stateUC,
	}
}

func (h *QuestHandler) List(w http.ResponseWriter, r *http.Request) {
	maxUserID := r.URL.Query().Get("max_user_id")
	quests, err := h.listUC.Execute(r.Context(), maxUserID)
	if err != nil {
		handleUseCaseError(w, err)
		return
	}
	writeJSON(w, http.StatusOK, map[string]any{"items": quests})
}

func (h *QuestHandler) Start(w http.ResponseWriter, r *http.Request) {
	questID, err := parsePathInt64(r, "quest_id")
	if err != nil {
		writeJSON(w, http.StatusBadRequest, map[string]string{"error": "invalid quest_id"})
		return
	}
	var req dto.StartQuestRequest
	if err := decodeJSON(r, &req); err != nil {
		writeJSON(w, http.StatusBadRequest, map[string]string{"error": "invalid json"})
		return
	}
	result, err := h.startUC.Execute(r.Context(), botuc.StartQuestInput{
		MaxUserID: req.MaxUserID,
		QuestID:   questID,
	})
	if err != nil {
		handleUseCaseError(w, err)
		return
	}
	writeJSON(w, http.StatusOK, result)
}

func (h *QuestHandler) State(w http.ResponseWriter, r *http.Request) {
	questID, err := parsePathInt64(r, "quest_id")
	if err != nil {
		writeJSON(w, http.StatusBadRequest, map[string]string{"error": "invalid quest_id"})
		return
	}
	maxUserID := r.URL.Query().Get("max_user_id")
	state, err := h.stateUC.Execute(r.Context(), maxUserID, questID)
	if err != nil {
		handleUseCaseError(w, err)
		return
	}
	writeJSON(w, http.StatusOK, state)
}
