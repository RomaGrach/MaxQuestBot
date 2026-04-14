package security

import (
	"crypto/hmac"
	"crypto/sha256"
	"encoding/base64"
	"encoding/hex"
	"encoding/json"
	"errors"
	"strings"
	"time"
)

var (
	ErrInvalidToken = errors.New("invalid token")
	ErrTokenExpired = errors.New("token expired")
)

type Claims struct {
	AdminID   int64  `json:"admin_id"`
	Username  string `json:"username"`
	Role      string `json:"role"`
	ExpiresAt int64  `json:"exp"`
}

type TokenManager struct {
	secret []byte
	ttl    time.Duration
}

func NewTokenManager(secret string, ttl time.Duration) *TokenManager {
	return &TokenManager{
		secret: []byte(secret),
		ttl:    ttl,
	}
}

func (m *TokenManager) Issue(adminID int64, username, role string) (string, error) {
	claims := Claims{
		AdminID:   adminID,
		Username:  username,
		Role:      role,
		ExpiresAt: time.Now().Add(m.ttl).Unix(),
	}
	payloadRaw, err := json.Marshal(claims)
	if err != nil {
		return "", err
	}
	payload := base64.RawURLEncoding.EncodeToString(payloadRaw)
	return payload + "." + m.sign(payload), nil
}

func (m *TokenManager) Parse(token string) (Claims, error) {
	parts := strings.Split(token, ".")
	if len(parts) != 2 {
		return Claims{}, ErrInvalidToken
	}
	payload, signature := parts[0], parts[1]
	if !hmac.Equal([]byte(m.sign(payload)), []byte(signature)) {
		return Claims{}, ErrInvalidToken
	}

	payloadRaw, err := base64.RawURLEncoding.DecodeString(payload)
	if err != nil {
		return Claims{}, ErrInvalidToken
	}
	var claims Claims
	if err := json.Unmarshal(payloadRaw, &claims); err != nil {
		return Claims{}, ErrInvalidToken
	}
	if time.Now().Unix() > claims.ExpiresAt {
		return Claims{}, ErrTokenExpired
	}

	return claims, nil
}

func (m *TokenManager) sign(payload string) string {
	mac := hmac.New(sha256.New, m.secret)
	_, _ = mac.Write([]byte(payload))
	return hex.EncodeToString(mac.Sum(nil))
}
