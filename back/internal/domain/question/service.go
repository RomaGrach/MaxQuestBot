package question

import (
	"strings"
	"unicode"
)

type Matcher interface {
	Match(answer, correct string) bool
}

type SimpleMatcher struct{}

func (SimpleMatcher) Match(answer, correct string) bool {
	normAnswer := normalize(answer)
	normCorrect := normalize(correct)
	if normAnswer == "" || normCorrect == "" {
		return false
	}
	if normAnswer == normCorrect {
		return true
	}
	// MVP "по смыслу": разрешаем частичное совпадение без NLP.
	if len(normAnswer) >= 4 && strings.Contains(normCorrect, normAnswer) {
		return true
	}
	if len(normCorrect) >= 4 && strings.Contains(normAnswer, normCorrect) {
		return true
	}
	return false
}

func normalize(s string) string {
	replacer := strings.NewReplacer("ё", "е", "Ё", "Е")
	s = strings.ToLower(replacer.Replace(strings.TrimSpace(s)))
	var b strings.Builder
	b.Grow(len(s))
	lastSpace := false
	for _, r := range s {
		if unicode.IsLetter(r) || unicode.IsDigit(r) {
			b.WriteRune(r)
			lastSpace = false
			continue
		}
		if !lastSpace {
			b.WriteRune(' ')
			lastSpace = true
		}
	}
	return strings.TrimSpace(b.String())
}
