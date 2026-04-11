package scraper

import (
	"context"
	"fmt"
	"log"
	"regexp"
	"strings"
	"time"

	"github.com/PuerkitoBio/goquery"
	"github.com/asflum99/agenda-cultural/internal/models"
	"github.com/aws/aws-sdk-go-v2/aws"
	"github.com/gocolly/colly/v2"
)

type LUMScraper struct{}

func (s LUMScraper) Name() string {
	return "Lugar de la Memoria, la Toleración y la Inclusión Social"
}

func (s LUMScraper) GetMovies(ctx context.Context, cfg aws.Config) ([]models.Movie, error) {
	movieEventRegex := regexp.MustCompile(`(?i)cine`)
	movieTitleRegex := regexp.MustCompile(`(?i)^(.+)\s+de\s+(.+)$`)
	baseURL := "https://lum.cultura.pe/actividades"
	var lumMovies []models.Movie
	var count int
	c := NewBaseCollector("lum.cultura.pe")

	// Regla 1: Buscar agenda actual
	c.OnHTML(".view", func(h *colly.HTMLElement) {
		now := NowInPeru()
		currentMonth := monthEsp[now.Month()]
		currentYear := now.Year()
		target := fmt.Sprintf("Agenda %s %d", currentMonth, currentYear)

		// Itera sobre cada elemento que cumpla la condición de "span a"
		h.DOM.Find("span a").Each(func(i int, s *goquery.Selection) {
			textFound := strings.ToLower(strings.TrimSpace(s.Text()))
			if strings.Contains(textFound, strings.ToLower(target)) {
				link, exists := s.Attr("href")
				if exists {
					fullURL := h.Request.AbsoluteURL(link)
					h.Request.Visit(fullURL)
				}
			}
		})
	})

	// Regla 2: Buscar películas
	c.OnHTML("article", func(h *colly.HTMLElement) {
		count++
		movie := models.Movie{}

		// Itera sobre cada elemento que cumpla la condición de "p strong"
		h.DOM.Find("p strong").Each(func(i int, s *goquery.Selection) {
			if movieEventRegex.MatchString(s.Text()) {
				ulElement := s.Parent().Next()
				rawMovieTitle := ulElement.Find("strong").Text()
				if movieTitleRegex.MatchString(rawMovieTitle) {
					title := cleanMovieTitle(rawMovieTitle, movieTitleRegex)
					posterURL := FetchPosterURL(title, ctx, cfg)
					screeningInfo := ulElement.Next().Text()
					screeningInfoList := strings.Split(screeningInfo, "\n")
					date, err := parseDate(screeningInfoList)
					if err != nil {
						log.Printf("Error al parsear fecha %v", err)
						return
					}
					movie.Title = title
					movie.Location = "Lugar de la Memoria, la Tolerancia e Inclusión Social"
					movie.Date = date
					movie.CenterSlug = "lum"
					movie.PosterURL = posterURL
					movie.SourceURL = h.Request.URL.String()
					movie.CreatedAt = NowInPeru()

					lumMovies = append(lumMovies, movie)
				}
			}
		})
	})

	err := c.Visit(baseURL)

	return lumMovies, err
}

func parseDate(screeningInfoList []string) (time.Time, error) {
	dateStr := screeningInfoList[0]
	timeStr := screeningInfoList[1]

	timeStr = strings.ReplaceAll(timeStr, "p. m.", "PM")
	timeStr = strings.ReplaceAll(timeStr, "a. m.", "AM")
	timeStr = strings.TrimSpace(timeStr)

	year := time.Now().Year()
	fullDate := fmt.Sprintf("%s %d %s", dateStr, year, timeStr)

	englishDate := TranslateDateToEnglish(fullDate)

	layout := "Monday 2 January 2006 3:04 PM"

	loc, _ := time.LoadLocation("America/Lima")
	t, err := time.ParseInLocation(layout, englishDate, loc)

	return t, err
}

func cleanMovieTitle(rawMovieTitle string, movieTitleRegex *regexp.Regexp) string {
	match := movieTitleRegex.FindStringSubmatch(rawMovieTitle)

	if len(match) > 1 {
		return strings.TrimSpace(match[1])
	}

	return strings.TrimSpace(rawMovieTitle)
}
