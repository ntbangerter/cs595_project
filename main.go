package main

import (
	"bytes"
	"encoding/json"
	"io"
	"net/http"
	"log"
	"regexp"
	"strings"
	"time"
)


const OPENNODE_API_KEY = "ADD OPENNODE API KEY"


func extractValue(body string, key string) string {
	keystr := "\"" + key + "\":[^,;\\]}]*"
	r, _ := regexp.Compile(keystr)
	match := r.FindString(body)
	keyValMatch := strings.Split(match, ":")
	return strings.ReplaceAll(keyValMatch[1], "\"", "")
}


type ONCreatePaymentResponse struct {
	Data struct {
		ID                string  `json:"id"`
		Description       string  `json:"description"`
		DescHash          bool    `json:"desc_hash"`
		CreatedAt         int     `json:"created_at"`
		Status            string  `json:"status"`
		Amount            int     `json:"amount"`
		CallbackURL       any     `json:"callback_url"`
		SuccessURL        any     `json:"success_url"`
		HostedCheckoutURL string  `json:"hosted_checkout_url"`
		OrderID           any     `json:"order_id"`
		Currency          string  `json:"currency"`
		SourceFiatValue   float64 `json:"source_fiat_value"`
		FiatValue         float64 `json:"fiat_value"`
		AutoSettle        bool    `json:"auto_settle"`
		NotifEmail        any     `json:"notif_email"`
		Address           string  `json:"address"`
		Metadata          struct {
		} `json:"metadata"`
		ChainInvoice struct {
			Address string `json:"address"`
		} `json:"chain_invoice"`
		URI              string `json:"uri"`
		TTL              int    `json:"ttl"`
		LightningInvoice struct {
			ExpiresAt int    `json:"expires_at"`
			Payreq    string `json:"payreq"`
		} `json:"lightning_invoice"`
	} `json:"data"`
}


func createPayment() string {

	url := "https://dev-api.opennode.com/v1/charges"
	
	requestBody := []byte(`{"amount": "0.01", "currency": "USD"}`)

	req, _ := http.NewRequest("POST", url, bytes.NewBuffer(requestBody))

	req.Header.Add("accept", "application/json")
	req.Header.Add("Content-Type", "application/json")
	req.Header.Add("Authorization", OPENNODE_API_KEY)

	res, _ := http.DefaultClient.Do(req)

	defer res.Body.Close()
	body, _ := io.ReadAll(res.Body)

	var response ONCreatePaymentResponse
	json.Unmarshal(body, &response)

	log.Printf("Response body: %s, %s, %s", response.Data.ID, string(response.Data.Amount), response.Data.HostedCheckoutURL)

	return response.Data.ID
}


type CreatePaymentResponse struct {
	ID string
}


type OpenNodeTransaction struct {
	Data struct {
		ID          string    `json:"id"`
		Description string    `json:"description"`
		Price       int       `json:"price"`
		Status      string    `json:"status"`
		CreatedAt   time.Time `json:"created_at"`
		Fee         int       `json:"fee"`
		FiatValue   float64   `json:"fiat_value"`
		Notes       any       `json:"notes"`
		OrderID     any       `json:"order_id"`
		Onchain     []any     `json:"onchain"`
		Lightning   struct {
			ID         string    `json:"id"`
			Status     string    `json:"status"`
			Price      int       `json:"price"`
			Payreq     string    `json:"payreq"`
			CreatedAt  time.Time `json:"created_at"`
			ExpiresAt  time.Time `json:"expires_at"`
			SettledAt  time.Time `json:"settled_at"`
			CheckoutID string    `json:"checkout_id"`
		} `json:"lightning"`
		Metadata struct {
		} `json:"metadata"`
		Address           string    `json:"address"`
		Exchanged         bool      `json:"exchanged"`
		NetFiatValue      float64   `json:"net_fiat_value"`
		MissingAmt        int       `json:"missing_amt"`
		SettledAt         time.Time `json:"settled_at"`
		PaymentMethod     string    `json:"payment_method"`
		TTL               int       `json:"ttl"`
		DescHash          bool      `json:"desc_hash"`
		HostedCheckoutURL string    `json:"hosted_checkout_url"`
		CustomerSiteID    any       `json:"customer_site_id"`
	} `json:"data"`
}


func isPaid(id string) bool {
	url := "https://dev-api.opennode.com/v2/charge/" + id

	req, _ := http.NewRequest("GET", url, nil)

	req.Header.Add("accept", "application/json")
	req.Header.Add("Content-Type", "application/json")
	req.Header.Add("Authorization", OPENNODE_API_KEY)

	res, _ := http.DefaultClient.Do(req)

	defer res.Body.Close()
	body, _ := io.ReadAll(res.Body)

	var response OpenNodeTransaction
	json.Unmarshal(body, &response)

	log.Printf("Lightning payment ID: %s, Status: %s", id, response.Data.Lightning.Status)
	
	return response.Data.Lightning.Status == "paid"
}

type IsPaidResponse struct {
	IsPaid bool
}


func main() {
	server := initializeServer()
	server.runServer()
}
