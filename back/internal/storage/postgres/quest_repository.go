package postgres

import (
	"context"
	"database/sql"
	"time"

	"github.com/RomaGrach/quest-bot-backend/internal/domain/common"
	"github.com/RomaGrach/quest-bot-backend/internal/domain/quest"
)

type QuestRepository struct {
	db *DB
}

func NewQuestRepository(db *DB) *QuestRepository {
	return &QuestRepository{db: db}
}

func (r *QuestRepository) List(ctx context.Context) ([]quest.Quest, error) {
	return r.listPostgres(ctx, "")
}

func (r *QuestRepository) ListPublished(ctx context.Context) ([]quest.Quest, error) {
	return r.listPostgres(ctx, `WHERE status = 'published'`)
}

func (r *QuestRepository) GetByID(ctx context.Context, id int64) (quest.Quest, error) {
	return r.getByIDPostgres(ctx, id)
}

func (r *QuestRepository) Create(ctx context.Context, q quest.Quest) (quest.Quest, error) {
	return r.createPostgres(ctx, q)
}

func (r *QuestRepository) Update(ctx context.Context, q quest.Quest) (quest.Quest, error) {
	return r.updatePostgres(ctx, q)
}

func (r *QuestRepository) Delete(ctx context.Context, id int64) error {
	result, err := r.db.sql.ExecContext(ctx, `DELETE FROM quests WHERE id = $1`, id)
	if err != nil {
		return err
	}
	affected, err := result.RowsAffected()
	if err != nil {
		return err
	}
	if affected == 0 {
		return common.ErrNotFound
	}
	return nil
}

func (r *QuestRepository) listPostgres(ctx context.Context, where string) ([]quest.Quest, error) {
	rows, err := r.db.sql.QueryContext(ctx, `
		SELECT id, title, description, status, start_point, prize_info,
			start_at, end_at, default_max_attempts, allow_retry_before_gift,
			created_at, updated_at
		FROM quests `+where+`
		ORDER BY id
	`)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	items := make([]quest.Quest, 0)
	for rows.Next() {
		q, err := scanQuest(rows)
		if err != nil {
			return nil, err
		}
		items = append(items, q)
	}
	return items, rows.Err()
}

func (r *QuestRepository) getByIDPostgres(ctx context.Context, id int64) (quest.Quest, error) {
	row := r.db.sql.QueryRowContext(ctx, `
		SELECT id, title, description, status, start_point, prize_info,
			start_at, end_at, default_max_attempts, allow_retry_before_gift,
			created_at, updated_at
		FROM quests
		WHERE id = $1
	`, id)
	q, err := scanQuest(row)
	if err != nil {
		return quest.Quest{}, mapSQLError(err)
	}
	return q, nil
}

func (r *QuestRepository) createPostgres(ctx context.Context, q quest.Quest) (quest.Quest, error) {
	now := time.Now()
	if q.CreatedAt.IsZero() {
		q.CreatedAt = now
	}
	if q.UpdatedAt.IsZero() {
		q.UpdatedAt = now
	}
	row := r.db.sql.QueryRowContext(ctx, `
		INSERT INTO quests (
			title, description, status, start_point, prize_info,
			start_at, end_at, default_max_attempts, allow_retry_before_gift,
			created_at, updated_at
		)
		VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
		RETURNING id, title, description, status, start_point, prize_info,
			start_at, end_at, default_max_attempts, allow_retry_before_gift,
			created_at, updated_at
	`, q.Title, q.Description, string(q.Status), q.StartPoint, q.PrizeInfo, q.StartAt, q.EndAt,
		q.DefaultMaxAttempts, q.AllowRetryBeforeGift, q.CreatedAt, q.UpdatedAt)
	return scanQuest(row)
}

func (r *QuestRepository) updatePostgres(ctx context.Context, q quest.Quest) (quest.Quest, error) {
	q.UpdatedAt = time.Now()
	row := r.db.sql.QueryRowContext(ctx, `
		UPDATE quests
		SET title = $2, description = $3, status = $4, start_point = $5, prize_info = $6,
			start_at = $7, end_at = $8, default_max_attempts = $9,
			allow_retry_before_gift = $10, updated_at = $11
		WHERE id = $1
		RETURNING id, title, description, status, start_point, prize_info,
			start_at, end_at, default_max_attempts, allow_retry_before_gift,
			created_at, updated_at
	`, q.ID, q.Title, q.Description, string(q.Status), q.StartPoint, q.PrizeInfo, q.StartAt, q.EndAt,
		q.DefaultMaxAttempts, q.AllowRetryBeforeGift, q.UpdatedAt)
	updated, err := scanQuest(row)
	if err != nil {
		return quest.Quest{}, mapSQLError(err)
	}
	return updated, nil
}

type questScanner interface {
	Scan(dest ...any) error
}

func scanQuest(row questScanner) (quest.Quest, error) {
	var q quest.Quest
	var status string
	var startAt sql.NullTime
	var endAt sql.NullTime

	err := row.Scan(
		&q.ID,
		&q.Title,
		&q.Description,
		&status,
		&q.StartPoint,
		&q.PrizeInfo,
		&startAt,
		&endAt,
		&q.DefaultMaxAttempts,
		&q.AllowRetryBeforeGift,
		&q.CreatedAt,
		&q.UpdatedAt,
	)
	if err != nil {
		return quest.Quest{}, err
	}
	q.Status = quest.Status(status)
	if startAt.Valid {
		q.StartAt = &startAt.Time
	}
	if endAt.Valid {
		q.EndAt = &endAt.Time
	}
	return q, nil
}
