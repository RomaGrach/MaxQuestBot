package bot

import (
	"io"
	"net/http"

	maxtransport "github.com/RomaGrach/quest-bot-backend/internal/transport/max"
)

type WebhookHandler struct {
	signer *maxtransport.Signer
}

func NewWebhookHandler(signer *maxtransport.Signer) *WebhookHandler {
	return &WebhookHandler{signer: signer}
}

func (h *WebhookHandler) Handle(w http.ResponseWriter, r *http.Request) {
	signature := r.Header.Get("X-MAX-Signature")
	body, _ := io.ReadAll(r.Body)

	if signature != "" && h.signer != nil && !h.signer.Verify(body, signature) {
		writeJSON(w, http.StatusUnauthorized, map[string]string{"error": "invalid signature"})
		return
	}

	// MVP: вебхук принят, разбор событий MAX можно расширить отдельно.
	writeJSON(w, http.StatusOK, map[string]string{"status": "accepted"})
}
