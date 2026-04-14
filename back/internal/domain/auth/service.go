package auth

type TokenIssuer interface {
	Issue(adminID int64, username, role string) (string, error)
}
