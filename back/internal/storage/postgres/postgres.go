package postgres

import (
	"sync"
	"time"

	"github.com/RomaGrach/quest-bot-backend/internal/domain/attempt"
	"github.com/RomaGrach/quest-bot-backend/internal/domain/auth"
	"github.com/RomaGrach/quest-bot-backend/internal/domain/quest"
	"github.com/RomaGrach/quest-bot-backend/internal/domain/question"
	"github.com/RomaGrach/quest-bot-backend/internal/domain/user"
)

type DB struct {
	mu sync.RWMutex

	nextQuestID    int64
	nextQuestionID int64
	nextUserID     int64
	nextAttemptID  int64
	nextAdminID    int64

	quests       map[int64]quest.Quest
	questions    map[int64]question.Question
	users        map[int64]user.User
	usersByMaxID map[string]int64
	attempts     map[int64]attempt.Attempt
	admins       map[int64]auth.Admin
	adminByLogin map[string]int64
}

func NewInMemoryDB(now time.Time) *DB {
	db := &DB{
		quests:       make(map[int64]quest.Quest),
		questions:    make(map[int64]question.Question),
		users:        make(map[int64]user.User),
		usersByMaxID: make(map[string]int64),
		attempts:     make(map[int64]attempt.Attempt),
		admins:       make(map[int64]auth.Admin),
		adminByLogin: make(map[string]int64),
	}
	db.seedMVP(now)
	return db
}

func (db *DB) seedMVP(now time.Time) {
	db.nextQuestID++
	questID := db.nextQuestID

	db.quests[questID] = quest.Quest{
		ID:                 questID,
		Title:              "Квест по парку",
		Description:        "Минимальный квест-прогулка из 3 вопросов.",
		Status:             quest.StatusPublished,
		StartPoint:         "Центральный вход в парк",
		PrizeInfo:          "Получите подарок у стойки организаторов с 10:00 до 20:00.",
		DefaultMaxAttempts: 3,
		CreatedAt:          now,
		UpdatedAt:          now,
	}

	questions := []question.Question{
		{
			QuestID:       questID,
			Order:         1,
			Context:       "В одном из уральских сказов есть образ Огневушки.",
			Task:          "Найдите памятник и отправьте слово с таблички.",
			CorrectAnswer: "Огневушка",
			Explanation:   "Огневушка-поскакушка в сказах Бажова считается знаком месторождения золота.",
			Hint:          "Ищите памятник девочке с длинной косой.",
		},
		{
			QuestID:       questID,
			Order:         2,
			Context:       "Следующая точка связана с историей основания города.",
			Task:          "Прочитайте слово на памятной табличке и отправьте его.",
			CorrectAnswer: "Основание",
			Explanation:   "Этот объект посвящен первым строителям города.",
			Hint:          "Поищите рядом с основной аллеей.",
		},
		{
			QuestID:       questID,
			Order:         3,
			Context:       "Финальная точка у старого фонтана.",
			Task:          "Как называется фонтан?",
			CorrectAnswer: "Дружба",
			Explanation:   "Фонтан 'Дружба' считается символом парка.",
			Hint:          "Название из одного слова на фронтальной табличке.",
		},
	}

	for _, q := range questions {
		db.nextQuestionID++
		q.ID = db.nextQuestionID
		db.questions[q.ID] = q
	}
}

func (db *DB) SeedAdmin(a auth.Admin) auth.Admin {
	db.mu.Lock()
	defer db.mu.Unlock()
	if id, ok := db.adminByLogin[a.Username]; ok {
		existing := db.admins[id]
		existing.PasswordHash = a.PasswordHash
		existing.Role = a.Role
		db.admins[id] = existing
		return existing
	}
	db.nextAdminID++
	a.ID = db.nextAdminID
	db.admins[a.ID] = a
	db.adminByLogin[a.Username] = a.ID
	return a
}
