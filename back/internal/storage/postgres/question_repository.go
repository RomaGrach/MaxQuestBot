package postgres

import (
	"context"
	"database/sql"

	"github.com/RomaGrach/quest-bot-backend/internal/domain/common"
	"github.com/RomaGrach/quest-bot-backend/internal/domain/question"
)

type QuestionRepository struct {
	db *DB
}

func NewQuestionRepository(db *DB) *QuestionRepository {
	return &QuestionRepository{db: db}
}

func (r *QuestionRepository) ListByQuestID(ctx context.Context, questID int64) ([]question.Question, error) {
	rows, err := r.db.sql.QueryContext(ctx, `
			SELECT id, quest_id, question_order, context, task, correct_answer,
				explanation, hint, semantic_mode, semantic_threshold, max_attempts
			FROM questions
			WHERE quest_id = $1
			ORDER BY question_order
		`, questID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	items := make([]question.Question, 0)
	for rows.Next() {
		q, err := scanQuestion(rows)
		if err != nil {
			return nil, err
		}
		items = append(items, q)
	}
	return items, rows.Err()
}

func (r *QuestionRepository) GetByQuestAndOrder(ctx context.Context, questID int64, order int) (question.Question, error) {
	row := r.db.sql.QueryRowContext(ctx, `
			SELECT id, quest_id, question_order, context, task, correct_answer,
				explanation, hint, semantic_mode, semantic_threshold, max_attempts
			FROM questions
			WHERE quest_id = $1 AND question_order = $2
		`, questID, order)
	q, err := scanQuestion(row)
	if err != nil {
		return question.Question{}, mapSQLError(err)
	}
	return q, nil
}

func (r *QuestionRepository) Create(ctx context.Context, q question.Question) (question.Question, error) {
	row := r.db.sql.QueryRowContext(ctx, `
			INSERT INTO questions (
				quest_id, question_order, context, task, correct_answer,
				explanation, hint, semantic_mode, semantic_threshold, max_attempts
			)
			VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
			RETURNING id, quest_id, question_order, context, task, correct_answer,
				explanation, hint, semantic_mode, semantic_threshold, max_attempts
		`, q.QuestID, q.Order, q.Context, q.Task, q.CorrectAnswer, q.Explanation,
		q.Hint, q.SemanticMode, q.SemanticThreshold, q.MaxAttempts)
	return scanQuestion(row)
}

func (r *QuestionRepository) Update(ctx context.Context, q question.Question) (question.Question, error) {
	row := r.db.sql.QueryRowContext(ctx, `
			UPDATE questions
			SET quest_id = $2, question_order = $3, context = $4, task = $5,
				correct_answer = $6, explanation = $7, hint = $8,
				semantic_mode = $9, semantic_threshold = $10, max_attempts = $11
			WHERE id = $1
			RETURNING id, quest_id, question_order, context, task, correct_answer,
				explanation, hint, semantic_mode, semantic_threshold, max_attempts
		`, q.ID, q.QuestID, q.Order, q.Context, q.Task, q.CorrectAnswer, q.Explanation,
		q.Hint, q.SemanticMode, q.SemanticThreshold, q.MaxAttempts)
	updated, err := scanQuestion(row)
	if err != nil {
		return question.Question{}, mapSQLError(err)
	}
	return updated, nil
}

func (r *QuestionRepository) Delete(ctx context.Context, id int64) error {
	result, err := r.db.sql.ExecContext(ctx, `DELETE FROM questions WHERE id = $1`, id)
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

type questionScanner interface {
	Scan(dest ...any) error
}

func scanQuestion(row questionScanner) (question.Question, error) {
	var q question.Question
	var maxAttempts sql.NullInt64
	err := row.Scan(
		&q.ID,
		&q.QuestID,
		&q.Order,
		&q.Context,
		&q.Task,
		&q.CorrectAnswer,
		&q.Explanation,
		&q.Hint,
		&q.SemanticMode,
		&q.SemanticThreshold,
		&maxAttempts,
	)
	if err != nil {
		return question.Question{}, err
	}
	if maxAttempts.Valid {
		value := int(maxAttempts.Int64)
		q.MaxAttempts = &value
	}
	return q, nil
}
