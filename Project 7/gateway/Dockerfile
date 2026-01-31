FROM golang:1.21-alpine AS builder

WORKDIR /app

# Install build dependencies
RUN apk add --no-cache git gcc musl-dev

# In a real implementation, we would install liboqs and oqs-openssl here
# RUN apk add --no-cache cmake make ninja
# RUN git clone --branch main https://github.com/open-quantum-safe/liboqs.git && \
#     cd liboqs && mkdir build && cd build && \
#     cmake -GNinja -DCMAKE_INSTALL_PREFIX=/usr/local .. && \
#     ninja && ninja install

# Copy Go module files and download dependencies
COPY go.mod go.sum* ./
RUN go mod download || true

# Copy source code
COPY . .

# Build the application
RUN go build -o pqc-gateway .

# Create a minimal runtime image
FROM alpine:latest

WORKDIR /app

# Install runtime dependencies
RUN apk add --no-cache ca-certificates

# Copy the binary from the builder stage
COPY --from=builder /app/pqc-gateway /app/

# Create self-signed certificates for development
RUN apk add --no-cache openssl && \
    openssl req -x509 -newkey rsa:4096 -keyout server.key -out server.crt -days 365 -nodes -subj '/CN=localhost' && \
    chmod 600 server.key

# Expose the SMTP port
EXPOSE 2525 8080

# Run the application
CMD ["/app/pqc-gateway"]