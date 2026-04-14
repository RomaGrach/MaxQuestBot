package observability

type Metrics struct{}

func NewMetrics() *Metrics {
	return &Metrics{}
}

func (m *Metrics) IncHTTPRequests(_ string, _ int) {}
