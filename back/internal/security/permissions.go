package security

const (
	RoleAdmin    = "admin"
	RoleOperator = "operator"
)

func CanManageQuests(role string) bool {
	return role == RoleAdmin
}

func CanManageUsers(role string) bool {
	return role == RoleAdmin
}

func CanMarkGift(role string) bool {
	return role == RoleAdmin || role == RoleOperator
}

func CanReadStats(role string) bool {
	return role == RoleAdmin || role == RoleOperator
}
