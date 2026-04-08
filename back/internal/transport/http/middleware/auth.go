package middleware

import (
	"context"
	"encoding/json"
	"net/http"
	"strings"

	"github.com/RomaGrach/quest-bot-backend/internal/security"
)

type claimsKey struct{}

func RequireAuth(tokens *security.TokenManager, allowedRoles ...string) func(http.Handler) http.Handler {
	allowed := make(map[string]struct{}, len(allowedRoles))
	for _, role := range allowedRoles {
		allowed[role] = struct{}{}
	}

	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			authHeader := r.Header.Get("Authorization")
			const prefix = "Bearer "
			if !strings.HasPrefix(authHeader, prefix) {
				writeAuthError(w, http.StatusUnauthorized, "missing bearer token")
				return
			}
			token := strings.TrimSpace(strings.TrimPrefix(authHeader, prefix))
			claims, err := tokens.Parse(token)
			if err != nil {
				writeAuthError(w, http.StatusUnauthorized, "invalid token")
				return
			}
			if len(allowed) > 0 {
				if _, ok := allowed[claims.Role]; !ok {
					writeAuthError(w, http.StatusForbidden, "insufficient permissions")
					return
				}
			}
			ctx := context.WithValue(r.Context(), claimsKey{}, claims)
			next.ServeHTTP(w, r.WithContext(ctx))
		})
	}
}

func ClaimsFromContext(ctx context.Context) (security.Claims, bool) {
	claims, ok := ctx.Value(claimsKey{}).(security.Claims)
	return claims, ok
}

func writeAuthError(w http.ResponseWriter, status int, message string) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(map[string]string{
		"error": message,
	})
}
