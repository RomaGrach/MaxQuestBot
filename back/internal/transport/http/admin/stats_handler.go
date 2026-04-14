package admin

import (
	"net/http"

	adminuc "github.com/RomaGrach/quest-bot-backend/internal/usecase/admin"
)

type StatsHandler struct {
	uc *adminuc.StatsUseCase
}

func NewStatsHandler(uc *adminuc.StatsUseCase) *StatsHandler {
	return &StatsHandler{uc: uc}
}

func (h *StatsHandler) Get(w http.ResponseWriter, r *http.Request) {
	stats, err := h.uc.Get(r.Context())
	if err != nil {
		handleUseCaseError(w, err)
		return
	}
	writeJSON(w, http.StatusOK, stats)
}

func (h *StatsHandler) ExportCSV(w http.ResponseWriter, r *http.Request) {
	content, err := h.uc.ExportCSV(r.Context())
	if err != nil {
		handleUseCaseError(w, err)
		return
	}
	w.Header().Set("Content-Type", "text/csv")
	w.Header().Set("Content-Disposition", "attachment; filename=stats.csv")
	w.WriteHeader(http.StatusOK)
	_, _ = w.Write(content)
}
