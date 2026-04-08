package admin

import (
	"net/http"

	"github.com/RomaGrach/quest-bot-backend/internal/domain/question"
	"github.com/RomaGrach/quest-bot-backend/internal/transport/http/dto"
	adminuc "github.com/RomaGrach/quest-bot-backend/internal/usecase/admin"
)

type QuestionHandler struct {
	uc *adminuc.QuestionUseCase
}

func NewQuestionHandler(uc *adminuc.QuestionUseCase) *QuestionHandler {
	return &QuestionHandler{uc: uc}
}

func (h *QuestionHandler) ListByQuest(w http.ResponseWriter, r *http.Request) {
	questID, err := parsePathInt64(r, "quest_id")
	if err != nil {
		writeJSON(w, http.StatusBadRequest, map[string]string{"error": "invalid quest_id"})
		return
	}
	items, err := h.uc.ListByQuest(r.Context(), questID)
	if err != nil {
		handleUseCaseError(w, err)
		return
	}
	writeJSON(w, http.StatusOK, map[string]any{"items": items})
}

func (h *QuestionHandler) Create(w http.ResponseWriter, r *http.Request) {
	questID, err := parsePathInt64(r, "quest_id")
	if err != nil {
		writeJSON(w, http.StatusBadRequest, map[string]string{"error": "invalid quest_id"})
		return
	}
	var req dto.CreateQuestionRequest
	if err := decodeJSON(r, &req); err != nil {
		writeJSON(w, http.StatusBadRequest, map[string]string{"error": "invalid json"})
		return
	}
	created, err := h.uc.Create(r.Context(), question.Question{
		QuestID:           questID,
		Order:             req.Order,
		Context:           req.Context,
		Task:              req.Task,
		CorrectAnswer:     req.CorrectAnswer,
		Explanation:       req.Explanation,
		Hint:              req.Hint,
		SemanticMode:      req.SemanticMode,
		SemanticThreshold: req.SemanticThreshold,
		MaxAttempts:       req.MaxAttempts,
	})
	if err != nil {
		handleUseCaseError(w, err)
		return
	}
	writeJSON(w, http.StatusCreated, created)
}

func (h *QuestionHandler) Update(w http.ResponseWriter, r *http.Request) {
	questionID, err := parsePathInt64(r, "question_id")
	if err != nil {
		writeJSON(w, http.StatusBadRequest, map[string]string{"error": "invalid question_id"})
		return
	}
	questID, err := parsePathInt64(r, "quest_id")
	if err != nil {
		writeJSON(w, http.StatusBadRequest, map[string]string{"error": "invalid quest_id"})
		return
	}

	var req dto.UpdateQuestionRequest
	if err := decodeJSON(r, &req); err != nil {
		writeJSON(w, http.StatusBadRequest, map[string]string{"error": "invalid json"})
		return
	}
	updated, err := h.uc.Update(r.Context(), question.Question{
		ID:                questionID,
		QuestID:           questID,
		Order:             req.Order,
		Context:           req.Context,
		Task:              req.Task,
		CorrectAnswer:     req.CorrectAnswer,
		Explanation:       req.Explanation,
		Hint:              req.Hint,
		SemanticMode:      req.SemanticMode,
		SemanticThreshold: req.SemanticThreshold,
		MaxAttempts:       req.MaxAttempts,
	})
	if err != nil {
		handleUseCaseError(w, err)
		return
	}
	writeJSON(w, http.StatusOK, updated)
}

func (h *QuestionHandler) Delete(w http.ResponseWriter, r *http.Request) {
	questionID, err := parsePathInt64(r, "question_id")
	if err != nil {
		writeJSON(w, http.StatusBadRequest, map[string]string{"error": "invalid question_id"})
		return
	}
	if err := h.uc.Delete(r.Context(), questionID); err != nil {
		handleUseCaseError(w, err)
		return
	}
	w.WriteHeader(http.StatusNoContent)
}
