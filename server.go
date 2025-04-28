package main

import (
	"encoding/json"
	"log"
	"net/http"
	"slices"
	"sync"
)


type Server struct {
	mu sync.Mutex
	valid_ids []string
	paid_status map[string]bool
	PORT string
}

func initializeServer() *Server {
	valid_ids := []string{}
	paid_status := make(map[string]bool)

	server := &Server{
		valid_ids: valid_ids,
		paid_status: paid_status,
		PORT: ":8080",
	}

	return server
}

func (server *Server) createPayment() string {
	id := createPayment()

	server.mu.Lock()
	server.valid_ids = append(server.valid_ids, id)
	server.paid_status[id] = false
	server.mu.Unlock()

	return id
}


func (server *Server) isPaid(id string) bool {

	isValid := server.isValid(id)

	if !isValid {
		return false
	}
	
	server.mu.Lock()

	payment_status := server.paid_status[id]

	if payment_status {
		server.mu.Unlock()
		return true
	}

	payment_status = isPaid(id)
	server.paid_status[id] = payment_status
	
	server.mu.Unlock()
	return payment_status
}

func (server *Server) isValid(id string) bool {
	server.mu.Lock()
	isValidID := slices.Contains(server.valid_ids, id)
	server.mu.Unlock()

	return isValidID
}


func (server *Server) handleCreatePayment(w http.ResponseWriter, r *http.Request) {
	log.Println("handleCreatePayment called")
	
	id := server.createPayment()

	w.Header().Set("Content-Type", "application/json")

	response := CreatePaymentResponse{
		ID: id,
	}

	json.NewEncoder(w).Encode(response)
}


func (server *Server) handleIsPaid(w http.ResponseWriter, r *http.Request) {
	id := r.URL.Query().Get("id")

	log.Printf("handleIsPaid called, ID: %s", id)

	w.Header().Set("Content-Type", "application/json")

	response := IsPaidResponse{
		IsPaid: server.isPaid(id),
	}

	json.NewEncoder(w).Encode(response)
}


func (server *Server) handleIsValid(w http.ResponseWriter, r *http.Request) {
	id := r.URL.Query().Get("id")

	log.Printf("handleIsValid called, ID: %s", id)

	w.Header().Set("Content-Type", "application/json")

	response := IsPaidResponse{
		IsPaid: server.isValid(id),
	}

	json.NewEncoder(w).Encode(response)
}


func (server *Server) runServer() {
	http.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		http.ServeFile(w, r, "index.html")
	})

	http.HandleFunc("/js", func(w http.ResponseWriter, r *http.Request) {
		http.ServeFile(w, r, "script.js")
	})

	http.HandleFunc("/ads/banner.jpg", func(w http.ResponseWriter, r *http.Request) {
		http.ServeFile(w, r, "ads/banner.jpg")
	})
	http.HandleFunc("/ads/inline.jpg", func(w http.ResponseWriter, r *http.Request) {
		http.ServeFile(w, r, "ads/inline.jpg")
	})
	http.HandleFunc("/ads/sidebar.jpg", func(w http.ResponseWriter, r *http.Request) {
		http.ServeFile(w, r, "ads/sidebar.jpg")
	})

	http.HandleFunc("/api/create-payment", server.handleCreatePayment)
	http.HandleFunc("/api/is-paid", server.handleIsPaid)
	http.HandleFunc("/api/is-valid", server.handleIsValid)

	// Start the server
	log.Printf("Starting server on http://localhost%s\n", server.PORT)
	if err := http.ListenAndServe(server.PORT, nil); err != nil {
		log.Fatalf("ListenAndServe: %v", err)
	}
}
