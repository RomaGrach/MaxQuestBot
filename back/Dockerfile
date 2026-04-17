FROM golang:1.26-alpine AS build

WORKDIR /app

COPY go.mod go.sum ./
RUN go mod download

COPY . .

RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -o /quest-bot-backend ./cmd/app

FROM alpine:3.21

WORKDIR /app
COPY --from=build /quest-bot-backend /quest-bot-backend

EXPOSE 8080

CMD ["/quest-bot-backend"]