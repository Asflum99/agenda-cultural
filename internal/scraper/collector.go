package scraper

import (
	"crypto/tls"
	"net/http"
	"time"

	"github.com/gocolly/colly/v2"
)

const (
	UserAgent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) " +
		"AppleWebKit/537.36 (KHTML, like Gecko) " +
		"Chrome/120.0.0.0 Safari/537.36"
)

func NewBaseCollector(domain ...string) *colly.Collector {
	c := colly.NewCollector(
		colly.AllowedDomains(domain...),
		colly.UserAgent(UserAgent),
	)

	c.WithTransport(&http.Transport{
		TLSClientConfig: &tls.Config{InsecureSkipVerify: true},
	})

	c.Limit(&colly.LimitRule{
		DomainGlob:  "*",
		RandomDelay: 2 * time.Second,
	})

	return c
}
