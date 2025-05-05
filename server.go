package main

import (
	"bytes"
	"encoding/json"
	"io"
	"log"
	"net/http"
	"slices"
	"sync"
)

const OPENAI_API_KEY = "ADD OPENAI API KEY"


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


type OpenAIResponse struct {
	ID                string `json:"id"`
	Object            string `json:"object"`
	CreatedAt         int    `json:"created_at"`
	Status            string `json:"status"`
	Error             any    `json:"error"`
	IncompleteDetails any    `json:"incomplete_details"`
	Instructions      any    `json:"instructions"`
	MaxOutputTokens   any    `json:"max_output_tokens"`
	Model             string `json:"model"`
	Output            []struct {
		ID      string `json:"id"`
		Type    string `json:"type"`
		Status  string `json:"status"`
		Content []struct {
			Type        string `json:"type"`
			Annotations []any  `json:"annotations"`
			Text        string `json:"text"`
		} `json:"content"`
		Role string `json:"role"`
	} `json:"output"`
	ParallelToolCalls  bool `json:"parallel_tool_calls"`
	PreviousResponseID any  `json:"previous_response_id"`
	Reasoning          struct {
		Effort  any `json:"effort"`
		Summary any `json:"summary"`
	} `json:"reasoning"`
	ServiceTier string  `json:"service_tier"`
	Store       bool    `json:"store"`
	Temperature float64 `json:"temperature"`
	Text        struct {
		Format struct {
			Type string `json:"type"`
		} `json:"format"`
	} `json:"text"`
	ToolChoice string  `json:"tool_choice"`
	Tools      []any   `json:"tools"`
	TopP       float64 `json:"top_p"`
	Truncation string  `json:"truncation"`
	Usage      struct {
		InputTokens        int `json:"input_tokens"`
		InputTokensDetails struct {
			CachedTokens int `json:"cached_tokens"`
		} `json:"input_tokens_details"`
		OutputTokens        int `json:"output_tokens"`
		OutputTokensDetails struct {
			ReasoningTokens int `json:"reasoning_tokens"`
		} `json:"output_tokens_details"`
		TotalTokens int `json:"total_tokens"`
	} `json:"usage"`
	User     any `json:"user"`
	Metadata struct {
	} `json:"metadata"`
}


func (server *Server) callOpenAI(id string, url string, prompt string) string {
	if (!server.isPaid(id)) {
		return "Error: please pay the LN transaction before submitting your API request."
	}
	
	requestBody := []byte(`{"model":"gpt-4o-mini", "input":"` + prompt + `"}`)

	req, _ := http.NewRequest("POST", url, bytes.NewBuffer(requestBody))

	req.Header.Add("accept", "application/json")
	req.Header.Add("Content-Type", "application/json")
	req.Header.Add("Authorization", "Bearer " + OPENAI_API_KEY)

	res, err := http.DefaultClient.Do(req)

	if (err != nil) {
		panic(err)
	}

	defer res.Body.Close()
	body, _ := io.ReadAll(res.Body)

	var response OpenAIResponse
	json.Unmarshal(body, &response)

	log.Printf("Response body: %v", response)

	return response.Output[0].Content[0].Text
}


type LLMRequest struct {
	Message string `json:"message"`
}


func (server *Server) handleCallLLM(w http.ResponseWriter, r *http.Request) {
	// Get ID from header
	id := r.Header.Get("id")
	if id == "" {
		http.Error(w, "ID header is required", http.StatusBadRequest)
		return
	}

	// Read the request body
	body, err := io.ReadAll(r.Body)
	if err != nil {
		http.Error(w, "Unable to read request body", http.StatusInternalServerError)
		return
	}
	defer r.Body.Close()

	// Parse the request body as JSON
	var data LLMRequest
	if err := json.Unmarshal(body, &data); err != nil {
		http.Error(w, "Invalid request payload", http.StatusBadRequest)
		return
	}

	response := server.callOpenAI(id, "https://api.openai.com/v1/responses", data.Message)

	json.NewEncoder(w).Encode(response)
}


func (server *Server) handleCallvLLM(w http.ResponseWriter, r *http.Request) {
	// Get ID from header
	id := r.Header.Get("id")
	if id == "" {
		http.Error(w, "ID header is required", http.StatusBadRequest)
		return
	}

	// Read the request body
	body, err := io.ReadAll(r.Body)
	if err != nil {
		http.Error(w, "Unable to read request body", http.StatusInternalServerError)
		return
	}
	defer r.Body.Close()

	// Parse the request body as JSON
	var data LLMRequest
	if err := json.Unmarshal(body, &data); err != nil {
		http.Error(w, "Invalid request payload", http.StatusBadRequest)
		return
	}

	response := server.callOpenAI(id, "http://192.168.0.96:8000/v1/completions", data.Message)

	json.NewEncoder(w).Encode(response)
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

	http.HandleFunc("/llm-demo", func(w http.ResponseWriter, r *http.Request) {
		http.ServeFile(w, r, "llm.html")
	})

	http.HandleFunc("/api/create-payment", server.handleCreatePayment)
	http.HandleFunc("/api/is-paid", server.handleIsPaid)
	http.HandleFunc("/api/is-valid", server.handleIsValid)

	http.HandleFunc("/api/call-llm1", server.handleCallLLM)
	http.HandleFunc("/api/call-llm2", server.handleCallvLLM)

	// Start the server
	log.Printf("Starting server on http://localhost%s\n", server.PORT)
	if err := http.ListenAndServe(server.PORT, nil); err != nil {
		log.Fatalf("ListenAndServe: %v", err)
	}
}
