package admin

import (
	"net/http"

	"github.com/RomaGrach/quest-bot-backend/internal/domain/quest"
	"github.com/RomaGrach/quest-bot-backend/internal/transport/http/dto"
	adminuc "github.com/RomaGrach/quest-bot-backend/internal/usecase/admin"
)

type QuestHandler struct {
	uc *adminuc.QuestUseCase
}

func NewQuestHandler(uc *adminuc.QuestUseCase) *QuestHandler {
	return &QuestHandler{uc: uc}
}

func (h *QuestHandler) List(w http.ResponseWriter, r *http.Request) {
	list, err := h.uc.List(r.Context())
	if err != nil {
		handleUseCaseError(w, err)
		return
	}
	writeJSON(w, http.StatusOK, map[string]any{"items": list})
}

func (h *QuestHandler) Create(w http.ResponseWriter, r *http.Request) {
	var req dto.CreateQuestRequest
	if err := decodeJSON(r, &req); err != nil {
		writeJSON(w, http.StatusBadRequest, map[string]string{"error": "invalid json"})
		return
	}
	created, err := h.uc.Create(r.Context(), quest.Quest{
		Title:                req.Title,
		Description:          req.Description,
		Status:               quest.Status(req.Status),
		StartPoint:           req.StartPoint,
		PrizeInfo:            req.PrizeInfo,
		StartAt:              req.StartAt,
		EndAt:                req.EndAt,
		DefaultMaxAttempts:   req.DefaultMaxAttempts,
		AllowRetryBeforeGift: req.AllowRetryBeforeGift,
	})
	if err != nil {
		handleUseCaseError(w, err)
		return
	}
	writeJSON(w, http.StatusCreated, created)
}

func (h *QuestHandler) Update(w http.ResponseWriter, r *http.Request) {
	questID, err := parsePathInt64(r, "quest_id")
	if err != nil {
		writeJSON(w, http.StatusBadRequest, map[string]string{"error": "invalid quest_id"})
		return
	}

	var req dto.UpdateQuestRequest
	if err := decodeJSON(r, &req); err != nil {
		writeJSON(w, http.StatusBadRequest, map[string]string{"error": "invalid json"})
		return
	}

	updated, err := h.uc.Update(r.Context(), quest.Quest{
		ID:                   questID,
		Title:                req.Title,
		Description:          req.Description,
		Status:               quest.Status(req.Status),
		StartPoint:           req.StartPoint,
		PrizeInfo:            req.PrizeInfo,
		StartAt:              req.StartAt,
		EndAt:                req.EndAt,
		DefaultMaxAttempts:   req.DefaultMaxAttempts,
		AllowRetryBeforeGift: req.AllowRetryBeforeGift,
	})
	if err != nil {
		handleUseCaseError(w, err)
		return
	}
	writeJSON(w, http.StatusOK, updated)
}

func (h *QuestHandler) Delete(w http.ResponseWriter, r *http.Request) {
	questID, err := parsePathInt64(r, "quest_id")
	if err != nil {
		writeJSON(w, http.StatusBadRequest, map[string]string{"error": "invalid quest_id"})
		return
	}
	if err := h.uc.Delete(r.Context(), questID); err != nil {
		handleUseCaseError(w, err)
		return
	}
	w.WriteHeader(http.StatusNoContent)
}
