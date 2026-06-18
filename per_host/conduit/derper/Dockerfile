FROM golang:1.23-alpine AS builder
RUN go install tailscale.com/cmd/derper@latest

FROM alpine:3.21
RUN apk add --no-cache ca-certificates openssl
COPY --from=builder /go/bin/derper /usr/local/bin/derper

# Entrypoint generates a self-signed cert on first run (derper requires
# one even when behind a reverse proxy that terminates TLS).  Caddy
# connects to derper over plain HTTP internally — the cert is only
# used to satisfy derper's startup requirement, not for client trust.
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8080 3478/udp
ENTRYPOINT ["/entrypoint.sh"]
