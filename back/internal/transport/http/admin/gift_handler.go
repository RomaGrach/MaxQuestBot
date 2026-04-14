package admin

import (
	"net/http"

	"github.com/RomaGrach/quest-bot-backend/internal/transport/http/dto"
	"github.com/RomaGrach/quest-bot-backend/internal/transport/http/middleware"
	adminuc "github.com/RomaGrach/quest-bot-backend/internal/usecase/admin"
)

type GiftHandler struct {
	uc *adminuc.GiftUseCase
}

func NewGiftHandler(uc *adminuc.GiftUseCase) *GiftHandler {
	return &GiftHandler{uc: uc}
}

func (h *GiftHandler) MarkIssued(w http.ResponseWriter, r *http.Request) {
	attemptID, err := parsePathInt64(r, "attempt_id")
	if err != nil {
		writeJSON(w, http.StatusBadRequest, map[string]string{"error": "invalid attempt_id"})
		return
	}
	claims, ok := middleware.ClaimsFromContext(r.Context())
	if !ok {
		writeJSON(w, http.StatusUnauthorized, map[string]string{"error": "missing claims"})
		return
	}
	var req dto.MarkGiftRequest
	if err := decodeJSON(r, &req); err != nil {
		writeJSON(w, http.StatusBadRequest, map[string]string{"error": "invalid json"})
		return
	}
	updated, err := h.uc.MarkIssued(r.Context(), adminuc.MarkGiftInput{
		AttemptID:     attemptID,
		IssuerAdminID: claims.AdminID,
		Comment:       req.Comment,
	})
	if err != nil {
		handleUseCaseError(w, err)
		return
	}
	writeJSON(w, http.StatusOK, updated)
}
