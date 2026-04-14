package security

import (
	"crypto/sha256"
	"encoding/hex"
)

type PasswordHasher interface {
	Hash(password string) string
	Compare(hash, password string) bool
}

type SHA256Hasher struct {
	salt string
}

func NewSHA256Hasher(salt string) *SHA256Hasher {
	return &SHA256Hasher{salt: salt}
}

func (h *SHA256Hasher) Hash(password string) string {
	sum := sha256.Sum256([]byte(h.salt + ":" + password))
	return hex.EncodeToString(sum[:])
}

func (h *SHA256Hasher) Compare(hash, password string) bool {
	return hash == h.Hash(password)
}
