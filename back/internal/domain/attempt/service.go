package attempt

func EnsureAttemptsMap(a Attempt) Attempt {
	if a.AttemptsByQuestion == nil {
		a.AttemptsByQuestion = make(map[int]int)
	}
	return a
}
