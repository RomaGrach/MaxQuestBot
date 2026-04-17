package postgres

import (
	"context"
	"database/sql"
	"errors"
	"time"

	"github.com/RomaGrach/quest-bot-backend/internal/domain/common"
	_ "github.com/jackc/pgx/v5/stdlib"
)

type DB struct {
	sql *sql.DB
}

func Open(ctx context.Context, databaseURL string) (*DB, error) {
	db, err := sql.Open("pgx", databaseURL)
	if err != nil {
		return nil, err
	}

	db.SetMaxOpenConns(10)
	db.SetMaxIdleConns(5)
	db.SetConnMaxLifetime(time.Hour)

	if err := db.PingContext(ctx); err != nil {
		_ = db.Close()
		return nil, err
	}

	return &DB{sql: db}, nil
}

func (db *DB) Close() error {
	if db == nil || db.sql == nil {
		return nil
	}
	return db.sql.Close()
}

func mapSQLError(err error) error {
	if err == nil {
		return nil
	}
	if errors.Is(err, sql.ErrNoRows) {
		return common.ErrNotFound
	}
	return err
}