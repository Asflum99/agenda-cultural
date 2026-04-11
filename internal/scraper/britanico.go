package scraper

import (
	"context"
	"fmt"
	"regexp"
	"strings"
	"time"

	"github.com/PuerkitoBio/goquery"
	"github.com/asflum99/agenda-cultural/internal/models"
	"github.com/aws/aws-sdk-go-v2/aws"
	"github.com/gocolly/colly/v2"
)

type BritanicoScraper struct{}

type venueRule struct {
	keyword     string
	replacement string
	isExclusive bool
}

var britanicoVenues = []venueRule{
	{
		keyword:     "cultural station",
		replacement: "Calle Bellavista 538 (Miraflores)",
		isExclusive: false,
	},
	{
		keyword:     "los jardines",
		replacement: "Auditorio Los Jardines - Alfredo Mendiola 1200 (SMP)",
		isExclusive: true,
	},
	{
		keyword:     "san borja",
		replacement: "Av. Javier Pardo Este 2726",
		isExclusive: false,
	},
	{
		keyword:     "pueblo libre",
		replacement: "Av. Bolívar 598",
		isExclusive: false,
	},
}

var cinePrefixRegex = regexp.MustCompile(`(?i)^cine:\s`)

func (s BritanicoScraper) Name() string { return "Británico Cultural" }

func (s BritanicoScraper) GetMovies(ctx context.Context, cfg aws.Config) ([]models.Movie, error) {
	baseURL := "https://britanico.edu.pe/cultural/eventos/?categoria=cine"
	var britanicoMovies []models.Movie
	c := NewBaseCollector("britanico.edu.pe")

	// Regla 1: Buscar enlaces de películas
	c.OnHTML(".wp-block-britanico-eventos-listado-eventos-filtro__item", func(h *colly.HTMLElement) {
		anchor := h.DOM.Find("a")
		link, exists := anchor.Attr("href")
		if exists {
			absLink := h.Request.AbsoluteURL(link)
			h.Request.Visit(absLink)
		}
	})

	// Regla 2: Extraer información de películas
	c.OnHTML(".wp-block-britanico-content-with-menu__container", func(h *colly.HTMLElement) {
		// Evalua si la película es gratuita
		freeEntry := h.DOM.Find("aside .wp-block-button__link").Text()
		if !strings.Contains(strings.ToLower(freeEntry), "gratuito") {
			return
		}

		rows := h.DOM.Find("tbody tr")
		columns := h.DOM.Find("tr th")

		if columns.Length() > 3 {
			// CASO A: Múltiples películas en tabla
			rows.Each(func(_ int, sel *goquery.Selection) {
				movie := s.parseMovieFactory(
					h,
					sel.Find("td").Eq(0).Text(), // Title
					sel.Find("td").Eq(1).Text(), // Date
					sel.Find("td").Eq(2).Text(), // Hour
					sel.Find("td").Eq(3).Text(), // Location
					ctx,
					cfg,
				)
				if movie != nil {
					britanicoMovies = append(britanicoMovies, *movie)
				}
			})
		} else {
			// CASO B: Una sola película
			movieTitle := h.DOM.Find("h2.wp-block-post-title").Text()

			// En caso sea una película con varias funciones
			rows.Each(func(_ int, sel *goquery.Selection) {
				movie := s.parseMovieFactory(
					h,
					movieTitle,
					sel.Find("td").Eq(0).Text(), // Date
					sel.Find("td").Eq(1).Text(), // Hour
					sel.Find("td").Eq(2).Text(), // Location
					ctx,
					cfg,
				)
				if movie != nil {
					britanicoMovies = append(britanicoMovies, *movie)
				}
			})
		}
	})

	err := c.Visit(baseURL)

	return britanicoMovies, err
}

func (s BritanicoScraper) parseDate(rawDate string) (time.Time, error) {
	r := strings.NewReplacer(" de ", " ")
	cleanDate := r.Replace(rawDate)
	cleanDate = TranslateDateToEnglish(cleanDate)

	loc, err := time.LoadLocation("America/Lima")
	if err != nil {
		return time.Time{}, err
	}

	layout := "Monday 2 January 2006 3:04 PM"
	return time.ParseInLocation(layout, cleanDate, loc)
}

func (s BritanicoScraper) parseMovieFactory(h *colly.HTMLElement, title, dateRaw, hour, location string, ctx context.Context, cfg aws.Config) *models.Movie {
	cleanTitle := cinePrefixRegex.ReplaceAllString(strings.TrimSpace(title), "")

	fullDateRaw := fmt.Sprintf("%s %s", strings.TrimSpace(dateRaw), strings.TrimSpace(hour))
	date, err := s.parseDate(fullDateRaw)
	if err != nil {
		fmt.Printf("❌ Error parseando fecha (%s): %v\n", title, err)
	}

	cleanLocation := s.cleanBritanicoLocation(location)

	movie := BuildMovie(
		strings.TrimSpace(cleanTitle),
		strings.TrimSpace(cleanLocation),
		"britanico",
		"Británico Cultural",
		h.Request.URL.String(),
		date,
		ctx,
		cfg,
	)

	if movie == nil {
		fmt.Printf("⏭️ Saltando película pasada: %s\n", title)
	}

	return movie
}

func (s BritanicoScraper) cleanBritanicoLocation(location string) string {
	location = strings.TrimSpace(location)
	lowerLoc := strings.ToLower(location)

	for _, rule := range britanicoVenues {
		if strings.Contains(lowerLoc, rule.keyword) {
			if rule.isExclusive {
				return rule.replacement
			}
			return fmt.Sprintf("%s - %s", location, rule.replacement)
		}
	}

	return location
}
