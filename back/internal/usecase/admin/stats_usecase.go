package admin

import (
	"bytes"
	"context"
	"encoding/csv"
	"strconv"

	"github.com/RomaGrach/quest-bot-backend/internal/domain/attempt"
	"github.com/RomaGrach/quest-bot-backend/internal/domain/user"
)

type StatsUseCase struct {
	users    user.Repository
	attempts attempt.Repository
}

func NewStatsUseCase(users user.Repository, attempts attempt.Repository) *StatsUseCase {
	return &StatsUseCase{
		users:    users,
		attempts: attempts,
	}
}

type Stats struct {
	Users      int `json:"users"`
	Attempts   int `json:"attempts"`
	Completed  int `json:"completed"`
	GiftIssued int `json:"gift_issued"`
}

func (uc *StatsUseCase) Get(ctx context.Context) (Stats, error) {
	users, err := uc.users.List(ctx)
	if err != nil {
		return Stats{}, err
	}
	attempts, err := uc.attempts.List(ctx)
	if err != nil {
		return Stats{}, err
	}

	stats := Stats{
		Users:    len(users),
		Attempts: len(attempts),
	}
	for _, a := range attempts {
		if a.Status == attempt.StatusCompleted {
			stats.Completed++
		}
		if a.GiftIssued() {
			stats.GiftIssued++
		}
	}
	return stats, nil
}

func (uc *StatsUseCase) ExportCSV(ctx context.Context) ([]byte, error) {
	users, err := uc.users.List(ctx)
	if err != nil {
		return nil, err
	}
	attempts, err := uc.attempts.List(ctx)
	if err != nil {
		return nil, err
	}

	userByID := make(map[int64]user.User, len(users))
	for _, u := range users {
		userByID[u.ID] = u
	}

	buf := &bytes.Buffer{}
	w := csv.NewWriter(buf)
	if err := w.Write([]string{
		"max_user_id",
		"phone",
		"quest_id",
		"status",
		"gift_issued",
	}); err != nil {
		return nil, err
	}

	for _, a := range attempts {
		u := userByID[a.UserID]
		if err := w.Write([]string{
			u.MaxUserID,
			u.Phone,
			strconv.FormatInt(a.QuestID, 10),
			string(a.Status),
			strconv.FormatBool(a.GiftIssued()),
		}); err != nil {
			return nil, err
		}
	}
	w.Flush()
	if err := w.Error(); err != nil {
		return nil, err
	}
	return buf.Bytes(), nil
}
