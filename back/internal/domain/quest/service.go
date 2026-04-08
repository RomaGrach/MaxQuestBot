package quest

import "time"

func IsAvailable(q Quest, now time.Time) bool {
	if q.Status != StatusPublished {
		return false
	}
	if q.StartAt != nil && now.Before(*q.StartAt) {
		return false
	}
	if q.EndAt != nil && now.After(*q.EndAt) {
		return false
	}
	return true
}
