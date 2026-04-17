package postgres

import (
	"context"
	"database/sql"
	"encoding/json"
	"time"

	"github.com/RomaGrach/quest-bot-backend/internal/domain/attempt"
)

type AttemptRepository struct {
	db *DB
}

func NewAttemptRepository(db *DB) *AttemptRepository {
	return &AttemptRepository{db: db}
}

func (r *AttemptRepository) List(ctx context.Context) ([]attempt.Attempt, error) {
	return r.listPostgres(ctx, "", nil)
}

func (r *AttemptRepository) ListByUserID(ctx context.Context, userID int64) ([]attempt.Attempt, error) {
	return r.listPostgres(ctx, "WHERE user_id = $1", []any{userID})
}

func (r *AttemptRepository) GetByID(ctx context.Context, id int64) (attempt.Attempt, error) {
	row := r.db.sql.QueryRowContext(ctx, attemptSelectSQL+` WHERE id = $1`, id)
	a, err := scanAttempt(row)
	if err != nil {
		return attempt.Attempt{}, mapSQLError(err)
	}
	return a, nil
}

func (r *AttemptRepository) GetByUserAndQuest(ctx context.Context, userID, questID int64) (attempt.Attempt, error) {
	row := r.db.sql.QueryRowContext(ctx, attemptSelectSQL+`
			WHERE user_id = $1 AND quest_id = $2
			ORDER BY started_at DESC, id DESC
			LIMIT 1
		`, userID, questID)
	a, err := scanAttempt(row)
	if err != nil {
		return attempt.Attempt{}, mapSQLError(err)
	}
	return a, nil
}

func (r *AttemptRepository) GetActiveByUserID(ctx context.Context, userID int64) (attempt.Attempt, error) {
	row := r.db.sql.QueryRowContext(ctx, attemptSelectSQL+`
			WHERE user_id = $1 AND status = $2
			ORDER BY started_at DESC, id DESC
			LIMIT 1
		`, userID, string(attempt.StatusInProgress))
	a, err := scanAttempt(row)
	if err != nil {
		return attempt.Attempt{}, mapSQLError(err)
	}
	return a, nil
}

func (r *AttemptRepository) Create(ctx context.Context, a attempt.Attempt) (attempt.Attempt, error) {
	if a.StartedAt.IsZero() {
		a.StartedAt = time.Now()
	}
	if a.AttemptsByQuestion == nil {
		a.AttemptsByQuestion = make(map[int]int)
	}
	attemptsJSON, err := json.Marshal(a.AttemptsByQuestion)
	if err != nil {
		return attempt.Attempt{}, err
	}
	row := r.db.sql.QueryRowContext(ctx, `
			INSERT INTO quest_attempts (
				user_id, quest_id, status, current_question_order, attempts_by_question,
				started_at, completed_at, gift_issued_at, gift_issued_by_admin_id, gift_comment
			)
			VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
			RETURNING id, user_id, quest_id, status, current_question_order, attempts_by_question,
				started_at, completed_at, gift_issued_at, gift_issued_by_admin_id, gift_comment
		`, a.UserID, a.QuestID, string(a.Status), a.CurrentQuestionOrder, attemptsJSON,
		a.StartedAt, a.CompletedAt, a.GiftIssuedAt, a.GiftIssuedByAdminID, a.GiftComment)
	return scanAttempt(row)
}

func (r *AttemptRepository) Update(ctx context.Context, a attempt.Attempt) (attempt.Attempt, error) {
	if a.AttemptsByQuestion == nil {
		a.AttemptsByQuestion = make(map[int]int)
	}
	attemptsJSON, err := json.Marshal(a.AttemptsByQuestion)
	if err != nil {
		return attempt.Attempt{}, err
	}
	row := r.db.sql.QueryRowContext(ctx, `
			UPDATE quest_attempts
			SET user_id = $2, quest_id = $3, status = $4, current_question_order = $5,
				attempts_by_question = $6, started_at = $7, completed_at = $8,
				gift_issued_at = $9, gift_issued_by_admin_id = $10, gift_comment = $11
			WHERE id = $1
			RETURNING id, user_id, quest_id, status, current_question_order, attempts_by_question,
				started_at, completed_at, gift_issued_at, gift_issued_by_admin_id, gift_comment
		`, a.ID, a.UserID, a.QuestID, string(a.Status), a.CurrentQuestionOrder,
		attemptsJSON, a.StartedAt, a.CompletedAt, a.GiftIssuedAt, a.GiftIssuedByAdminID, a.GiftComment)
	updated, err := scanAttempt(row)
	if err != nil {
		return attempt.Attempt{}, mapSQLError(err)
	}
	return updated, nil
}

const attemptSelectSQL = `
	SELECT id, user_id, quest_id, status, current_question_order, attempts_by_question,
		started_at, completed_at, gift_issued_at, gift_issued_by_admin_id, gift_comment
	FROM quest_attempts
`

func (r *AttemptRepository) listPostgres(ctx context.Context, where string, args []any) ([]attempt.Attempt, error) {
	rows, err := r.db.sql.QueryContext(ctx, attemptSelectSQL+" "+where+" ORDER BY id", args...)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	items := make([]attempt.Attempt, 0)
	for rows.Next() {
		a, err := scanAttempt(rows)
		if err != nil {
			return nil, err
		}
		items = append(items, a)
	}
	return items, rows.Err()
}

type attemptScanner interface {
	Scan(dest ...any) error
}

func scanAttempt(row attemptScanner) (attempt.Attempt, error) {
	var a attempt.Attempt
	var status string
	var attemptsJSON []byte
	var completedAt sql.NullTime
	var giftIssuedAt sql.NullTime
	var giftIssuedBy sql.NullInt64

	err := row.Scan(
		&a.ID,
		&a.UserID,
		&a.QuestID,
		&status,
		&a.CurrentQuestionOrder,
		&attemptsJSON,
		&a.StartedAt,
		&completedAt,
		&giftIssuedAt,
		&giftIssuedBy,
		&a.GiftComment,
	)
	if err != nil {
		return attempt.Attempt{}, err
	}
	a.Status = attempt.Status(status)
	if len(attemptsJSON) > 0 {
		if err := json.Unmarshal(attemptsJSON, &a.AttemptsByQuestion); err != nil {
			return attempt.Attempt{}, err
		}
	}
	if a.AttemptsByQuestion == nil {
		a.AttemptsByQuestion = make(map[int]int)
	}
	if completedAt.Valid {
		a.CompletedAt = &completedAt.Time
	}
	if giftIssuedAt.Valid {
		a.GiftIssuedAt = &giftIssuedAt.Time
	}
	if giftIssuedBy.Valid {
		value := giftIssuedBy.Int64
		a.GiftIssuedByAdminID = &value
	}
	return a, nil
}

func cloneAttempt(a attempt.Attempt) attempt.Attempt {
	if a.AttemptsByQuestion == nil {
		a.AttemptsByQuestion = make(map[int]int)
		return a
	}
	cp := make(map[int]int, len(a.AttemptsByQuestion))
	for k, v := range a.AttemptsByQuestion {
		cp[k] = v
	}
	a.AttemptsByQuestion = cp
	return a
}
