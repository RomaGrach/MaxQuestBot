package max

import (
	"crypto/hmac"
	"crypto/sha256"
	"encoding/hex"
)

type Signer struct {
	secret []byte
}

func NewSigner(secret string) *Signer {
	return &Signer{secret: []byte(secret)}
}

func (s *Signer) Verify(body []byte, signatureHex string) bool {
	mac := hmac.New(sha256.New, s.secret)
	_, _ = mac.Write(body)
	expected := mac.Sum(nil)

	got, err := hex.DecodeString(signatureHex)
	if err != nil {
		return false
	}
	return hmac.Equal(expected, got)
}
