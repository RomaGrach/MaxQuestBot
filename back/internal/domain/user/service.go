package user

import "strings"

func NormalizePhone(raw string) string {
	trimmed := strings.TrimSpace(raw)
	trimmed = strings.ReplaceAll(trimmed, " ", "")
	trimmed = strings.ReplaceAll(trimmed, "-", "")
	trimmed = strings.ReplaceAll(trimmed, "(", "")
	trimmed = strings.ReplaceAll(trimmed, ")", "")
	return trimmed
}
