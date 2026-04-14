package admin

import (
	"net/http"

	"github.com/RomaGrach/quest-bot-backend/internal/transport/http/dto"
	adminuc "github.com/RomaGrach/quest-bot-backend/internal/usecase/admin"
)

type AuthHandler struct {
	uc *adminuc.AuthUseCase
}

func NewAuthHandler(uc *adminuc.AuthUseCase) *AuthHandler {
	return &AuthHandler{uc: uc}
}

func (h *AuthHandler) Login(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		w.WriteHeader(http.StatusMethodNotAllowed)
		return
	}

	var req dto.AdminLoginRequest
	if err := decodeJSON(r, &req); err != nil {
		writeJSON(w, http.StatusBadRequest, map[string]string{"error": "invalid json"})
		return
	}

	result, err := h.uc.Login(r.Context(), adminuc.LoginInput{
		Username: req.Username,
		Password: req.Password,
	})
	if err != nil {
		handleUseCaseError(w, err)
		return
	}

	writeJSON(w, http.StatusOK, dto.AdminLoginResponse{
		Token:    result.Token,
		Username: result.Username,
		Role:     result.Role,
	})
}
