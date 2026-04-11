package models

import "time"

type Movie struct {
	Title      string    `json:"title" dynamodbav:"Title"`
	Location   string    `json:"location" dynamodbav:"Location"`
	Date       time.Time `json:"date" dynamodbav:"Date"`
	DateTitle  string    `json:"date_title" dynamodbav:"DateTitle"`
	CenterSlug string    `json:"center_slug" dynamodbav:"CenterSlug"`
	CenterName string    `json:"center_name" dynamodbav:"CenterName"`
	PosterURL  string    `json:"poster_url" dynamodbav:"PosterURL"`
	SourceURL  string    `json:"source_url" dynamodbav:"SourceURL"`
	CreatedAt  time.Time `json:"created_at" dynamodbav:"CreatedAt"`
	ExpiresAt  int64     `json:"expires_at" dynamodbav:"ExpiresAt"`
}
