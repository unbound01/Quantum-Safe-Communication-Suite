package main

import (
	"crypto/tls"
	"flag"
	"fmt"
	"io"
	"log"
	"net"
	"net/http"
	"os"
	"strings"
	"time"
)

// Configuration
var (
	listenAddr  = flag.String("listen", ":2525", "Address to listen on")
	postfixAddr = flag.String("postfix", "postfix:25", "Postfix server address")
	dovecotAddr = flag.String("dovecot", "dovecot:143", "Dovecot server address")
	receiptsURL = flag.String("receipts", "http://receipts:6000", "Receipts service URL")
	certFile    = flag.String("cert", "server.crt", "TLS certificate file")
	keyFile     = flag.String("key", "server.key", "TLS key file")
	debug       = flag.Bool("debug", true, "Enable debug logging")
)

// Simulated PQC functions (in production, these would use liboqs/oqs-openssl)
func getHybridTLSConfig() *tls.Config {
	// In a real implementation, this would configure oqs-openssl with hybrid X25519 + ML-KEM768
	// For this demo, we'll use standard TLS with a note about the hybrid config
	cert, err := tls.LoadX509KeyPair(*certFile, *keyFile)
	if err != nil {
		// For demo purposes, generate a self-signed cert if files don't exist
		log.Printf("Warning: Could not load TLS cert/key, would generate self-signed in production: %v", err)
		// In production: Use oqs-openssl to generate hybrid certificates
	}

	return &tls.Config{
		Certificates: []tls.Certificate{cert},
		CipherSuites: []uint16{
			tls.TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384,
			tls.TLS_ECDHE_ECDSA_WITH_AES_256_GCM_SHA384,
			// In production: Would include hybrid cipher suites from oqs-openssl
		},
		MinVersion: tls.VersionTLS12,
	}
}

// Simulated ML-DSA (Dilithium) signature function
func signWithDilithium(data []byte) []byte {
	// In production: Would use liboqs to generate a Dilithium signature
	// For demo, simulate with a placeholder
	return []byte(fmt.Sprintf("DILITHIUM-SIGNATURE-%x", data[:8]))
}

// Milter for email signing
func processMail(data []byte) []byte {
	// Simple milter that adds a signature header to outgoing emails
	lines := strings.Split(string(data), "\r\n")
	hasSubject := false
	modified := []string{}

	for _, line := range lines {
		modified = append(modified, line)
		if strings.HasPrefix(line, "Subject:") {
			hasSubject = true
		}
	}

	if hasSubject {
		// Add PQC signature header after subject
		sig := signWithDilithium(data)
		modified = append(modified, fmt.Sprintf("X-PQC-Signature: %s", sig))
		
		// Store receipt
		go storeReceipt(data, sig)
	}

	return []byte(strings.Join(modified, "\r\n"))
}

// Store receipt in the receipts service
func storeReceipt(data []byte, signature []byte) {
	// In production: Would make an HTTP request to the receipts service
	if *debug {
		log.Printf("Would store receipt for email with signature: %s", signature)
	}
	
	// Simple HTTP POST to receipts service (not implemented in this demo)
	// client := &http.Client{Timeout: 5 * time.Second}
	// _, err := client.Post(*receiptsURL + "/receipts", "application/json", bytes.NewBuffer(receiptData))
	// if err != nil {
	// 	log.Printf("Failed to store receipt: %v", err)
	// }
}

// Handle SMTP proxy connection
func handleConnection(clientConn net.Conn) {
	defer clientConn.Close()

	// Connect to backend Postfix server
	backendConn, err := net.Dial("tcp", *postfixAddr)
	if err != nil {
		log.Printf("Failed to connect to backend: %v", err)
		return
	}
	defer backendConn.Close()

	log.Printf("New connection from %s", clientConn.RemoteAddr())

	// Bidirectional copy with mail processing
	go func() {
		buf := make([]byte, 32*1024)
		for {
			n, err := clientConn.Read(buf)
			if err != nil {
				if err != io.EOF {
					log.Printf("Error reading from client: %v", err)
				}
				break
			}

			// Process outgoing mail (apply milter)
			processed := processMail(buf[:n])
			
			// Forward to backend
			_, err = backendConn.Write(processed)
			if err != nil {
				log.Printf("Error writing to backend: %v", err)
				break
			}
		}
	}()

	// Copy responses from backend to client
	io.Copy(clientConn, backendConn)
}

// Health check handler
func healthHandler(w http.ResponseWriter, r *http.Request) {
	fmt.Fprintf(w, "PQC Gateway healthy\n")
	fmt.Fprintf(w, "Using hybrid TLS: X25519 + ML-KEM768 (simulated)\n")
	fmt.Fprintf(w, "Using ML-DSA (Dilithium) for signatures (simulated)\n")
}

func main() {
	flag.Parse()

	// Start health check HTTP server
	go func() {
		http.HandleFunc("/health", healthHandler)
		log.Printf("Health check server listening on :8080")
		http.ListenAndServe(":8080", nil)
	}()

	// Create TLS listener
	config := getHybridTLSConfig()
	listener, err := tls.Listen("tcp", *listenAddr, config)
	if err != nil {
		// Fallback to non-TLS for demo purposes
		log.Printf("Warning: Failed to create TLS listener, falling back to non-TLS: %v", err)
		listener, err = net.Listen("tcp", *listenAddr)
		if err != nil {
			log.Fatalf("Failed to create listener: %v", err)
		}
	}

	log.Printf("PQC Email Gateway listening on %s", *listenAddr)
	log.Printf("Forwarding to Postfix at %s", *postfixAddr)

	// Accept connections
	for {
		conn, err := listener.Accept()
		if err != nil {
			log.Printf("Error accepting connection: %v", err)
			continue
		}
		go handleConnection(conn)
	}
}