package scraper

import (
	"context"
	"fmt"
	"regexp"
	"strings"
	"time"

	"github.com/asflum99/agenda-cultural/internal/models"
	"github.com/aws/aws-sdk-go-v2/aws"
	"github.com/gocolly/colly/v2"
)

type BNPScraper struct{}

var locationKeywords = regexp.MustCompile(`(?i)biblioteca|bnp`)

func (s BNPScraper) Name() string { return "Biblioteca Nacional del Perú" }

func (s BNPScraper) GetMovies(ctx context.Context, cfg aws.Config) ([]models.Movie, error) {
	baseURL := "https://eventos.bnp.gob.pe"
	var bnpMovies []models.Movie
	c := NewBaseCollector("eventos.bnp.gob.pe")

	// Regla 1: Busca enlaces de películas
	c.OnHTML(".bg-cineforum.categoria", func(h *colly.HTMLElement) {
		anchor := h.DOM.Closest("a")
		link, exists := anchor.Attr("href")
		if exists {
			absLink := h.Request.AbsoluteURL(link)
			h.Request.Visit(absLink)
		}
	})

	// Regla 2: Extrae información de la película
	c.OnHTML(".section-event-single-content", func(h *colly.HTMLElement) {
		// Extrae día y hora de proyección de la película
		dateElement := h.DOM.Find("#ContentPlaceHolder1_gpDetalleEvento")
		rawDate := dateElement.Find("p").Eq(1).Text()
		date, err := s.parseDate(rawDate)
		if err != nil {
			fmt.Printf("Error parseando fecha: %v", err)
			return
		}

		// Extrae dirección del local de proyección
		rawLocation := h.DOM.Find("#ContentPlaceHolder1_gpUbicacion p").Text()
		location := cleanLocation(rawLocation)

		// Extrae nombre de la película
		rawTitle := h.DOM.Parent().Find("#ContentPlaceHolder1_gpCabecera h1").Text()
		title := parseBNPTitle(rawTitle)

		if movie := BuildMovie(title, location, "bnp", "Biblioteca Nacional del Perú", h.Request.URL.String(), date, ctx, cfg); movie != nil {
			bnpMovies = append(bnpMovies, *movie)
		} else {
			fmt.Println("⏭️ Saltando película pasada")
		}
	})

	err := c.Visit(baseURL)

	return bnpMovies, err
}

func (s BNPScraper) parseDate(rawDate string) (time.Time, error) {
	parts := strings.Split(rawDate, ", ")
	if len(parts) < 2 {
		return time.Time{}, fmt.Errorf("formato de fecha inválido")
	}
	cleanDate := parts[1]

	r := strings.NewReplacer(" de ", " ", " del ", " ")
	cleanDate = r.Replace(cleanDate)
	cleanDate = strings.Join(strings.Fields(cleanDate), " ")
	cleanDate = TranslateDateToEnglish(cleanDate)

	loc, err := time.LoadLocation("America/Lima")
	if err != nil {
		return time.Time{}, err
	}

	layout := "2 January 2006 3:04PM"
	return time.ParseInLocation(layout, cleanDate, loc)
}

func parseBNPTitle(rawTitle string) string {
	rawTitle = strings.TrimSpace(rawTitle)
	index := strings.LastIndex(rawTitle, " (")

	if index == -1 {
		return rawTitle
	}

	title := rawTitle[:index]

	return title
}

func cleanLocation(location string) string {
	// Busca la posición de keywords (case-insensitive gracias a "(?!)")
	match := locationKeywords.FindStringIndex(location)
	if match == nil {
		return location
	}

	pos := match[0]
	result := location[pos:]

	result = strings.Replace(result, ",", " -", 1)

	result = strings.ReplaceAll(result, ", San Borja", " (San Borja)")

	return strings.TrimSpace(result)
}
