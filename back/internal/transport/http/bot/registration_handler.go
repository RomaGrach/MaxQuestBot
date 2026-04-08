package bot

import (
	"net/http"

	"github.com/RomaGrach/quest-bot-backend/internal/transport/http/dto"
	botuc "github.com/RomaGrach/quest-bot-backend/internal/usecase/bot"
)

type RegistrationHandler struct {
	uc *botuc.RegistrationUseCase
}

func NewRegistrationHandler(uc *botuc.RegistrationUseCase) *RegistrationHandler {
	return &RegistrationHandler{uc: uc}
}

func (h *RegistrationHandler) Register(w http.ResponseWriter, r *http.Request) {
	var req dto.RegisterRequest
	if err := decodeJSON(r, &req); err != nil {
		writeJSON(w, http.StatusBadRequest, map[string]string{"error": "invalid json"})
		return
	}
	registered, err := h.uc.Execute(r.Context(), botuc.RegisterInput{
		MaxUserID: req.MaxUserID,
		Phone:     req.Phone,
		Consent:   req.Consent,
	})
	if err != nil {
		handleUseCaseError(w, err)
		return
	}
	writeJSON(w, http.StatusCreated, registered)
}
