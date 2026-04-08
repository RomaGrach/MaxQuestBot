package bot

import (
	"net/http"

	"github.com/RomaGrach/quest-bot-backend/internal/transport/http/dto"
	botuc "github.com/RomaGrach/quest-bot-backend/internal/usecase/bot"
)

type AnswerHandler struct {
	answerUC *botuc.AnswerUseCase
	hintUC   *botuc.HintUseCase
}

func NewAnswerHandler(answerUC *botuc.AnswerUseCase, hintUC *botuc.HintUseCase) *AnswerHandler {
	return &AnswerHandler{
		answerUC: answerUC,
		hintUC:   hintUC,
	}
}

func (h *AnswerHandler) Submit(w http.ResponseWriter, r *http.Request) {
	questID, err := parsePathInt64(r, "quest_id")
	if err != nil {
		writeJSON(w, http.StatusBadRequest, map[string]string{"error": "invalid quest_id"})
		return
	}
	var req dto.AnswerRequest
	if err := decodeJSON(r, &req); err != nil {
		writeJSON(w, http.StatusBadRequest, map[string]string{"error": "invalid json"})
		return
	}
	result, err := h.answerUC.Execute(r.Context(), botuc.AnswerInput{
		MaxUserID: req.MaxUserID,
		QuestID:   questID,
		Answer:    req.Answer,
	})
	if err != nil {
		handleUseCaseError(w, err)
		return
	}
	writeJSON(w, http.StatusOK, result)
}

func (h *AnswerHandler) Hint(w http.ResponseWriter, r *http.Request) {
	questID, err := parsePathInt64(r, "quest_id")
	if err != nil {
		writeJSON(w, http.StatusBadRequest, map[string]string{"error": "invalid quest_id"})
		return
	}
	var req dto.HintRequest
	if err := decodeJSON(r, &req); err != nil {
		writeJSON(w, http.StatusBadRequest, map[string]string{"error": "invalid json"})
		return
	}
	result, err := h.hintUC.Execute(r.Context(), req.MaxUserID, questID)
	if err != nil {
		handleUseCaseError(w, err)
		return
	}
	writeJSON(w, http.StatusOK, result)
}
