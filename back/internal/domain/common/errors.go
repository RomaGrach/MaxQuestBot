package common

import "errors"

var (
	ErrNotFound      = errors.New("not found")
	ErrConflict      = errors.New("conflict")
	ErrValidation    = errors.New("validation error")
	ErrUnauthorized  = errors.New("unauthorized")
	ErrForbidden     = errors.New("forbidden")
	ErrInvalidState  = errors.New("invalid state")
	ErrQuestFinished = errors.New("quest already finished")
)
