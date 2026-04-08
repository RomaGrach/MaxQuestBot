package admin

import (
	"net/http"

	"github.com/RomaGrach/quest-bot-backend/internal/transport/http/dto"
	adminuc "github.com/RomaGrach/quest-bot-backend/internal/usecase/admin"
)

type UserHandler struct {
	uc *adminuc.UserUseCase
}

func NewUserHandler(uc *adminuc.UserUseCase) *UserHandler {
	return &UserHandler{uc: uc}
}

func (h *UserHandler) List(w http.ResponseWriter, r *http.Request) {
	items, err := h.uc.List(r.Context())
	if err != nil {
		handleUseCaseError(w, err)
		return
	}
	writeJSON(w, http.StatusOK, map[string]any{"items": items})
}

func (h *UserHandler) AttemptsByUser(w http.ResponseWriter, r *http.Request) {
	userID, err := parsePathInt64(r, "user_id")
	if err != nil {
		writeJSON(w, http.StatusBadRequest, map[string]string{"error": "invalid user_id"})
		return
	}
	items, err := h.uc.AttemptsByUser(r.Context(), userID)
	if err != nil {
		handleUseCaseError(w, err)
		return
	}
	writeJSON(w, http.StatusOK, map[string]any{"items": items})
}

func (h *UserHandler) UpdateComment(w http.ResponseWriter, r *http.Request) {
	userID, err := parsePathInt64(r, "user_id")
	if err != nil {
		writeJSON(w, http.StatusBadRequest, map[string]string{"error": "invalid user_id"})
		return
	}
	var req dto.UpdateUserCommentRequest
	if err := decodeJSON(r, &req); err != nil {
		writeJSON(w, http.StatusBadRequest, map[string]string{"error": "invalid json"})
		return
	}
	updated, err := h.uc.UpdateComment(r.Context(), userID, req.Comment)
	if err != nil {
		handleUseCaseError(w, err)
		return
	}
	writeJSON(w, http.StatusOK, updated)
}
