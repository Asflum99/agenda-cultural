package scraper

import (
	"context"
	"fmt"
	"os"
	"regexp"
	"strings"
	"sync"
	"time"
	"unicode"

	"github.com/asflum99/agenda-cultural/internal/models"
	"github.com/aws/aws-sdk-go-v2/aws"
	"github.com/aws/aws-sdk-go-v2/service/ssm"
	tmdb "github.com/cyruzin/golang-tmdb"
	"golang.org/x/text/runes"
	"golang.org/x/text/transform"
	"golang.org/x/text/unicode/norm"
)

var (
	tmdbClient *tmdb.Client
	once       sync.Once
)

func GetTMDBClient(ctx context.Context, cfg aws.Config) *tmdb.Client {
	once.Do(func() {
		// Local
		if key := os.Getenv("TMDB_API_KEY"); key != "" {
			client, err := tmdb.Init(key)
			if err != nil {
				fmt.Printf("No se pudo inicializar TMDB: %v", err)
				return
			}
			tmdbClient = client
			return
		}

		// Production
		ssmClient := ssm.NewFromConfig(cfg)
		result, err := ssmClient.GetParameter(ctx, &ssm.GetParameterInput{
			Name:           aws.String("/agenda-cultural/tmdb-api-key"),
			WithDecryption: aws.Bool(true),
		})
		if err != nil {
			fmt.Printf("No se pudo obtener la API key: %v", err)
			return
		}

		client, err := tmdb.Init(*result.Parameter.Value)
		if err != nil {
			fmt.Printf("No se pudo inicializar TMDB: %v", err)
			return
		}
		tmdbClient = client
	})
	return tmdbClient
}

func TranslateDateToEnglish(s string) string {
	s = strings.ReplaceAll(s, "p. m.", "PM")
	s = strings.ReplaceAll(s, "a. m.", "AM")
	s = strings.ReplaceAll(s, "P. M.", "PM")
	s = strings.ReplaceAll(s, "A. M.", "AM")
	s = strings.ReplaceAll(s, "p.m.", "PM")
	s = strings.ReplaceAll(s, "a.m.", "AM")

	replacer := strings.NewReplacer(
		// Meses (Título y minúscula)
		"Enero", "January", "enero", "January",
		"Febrero", "February", "febrero", "February",
		"Marzo", "March", "marzo", "March",
		"Abril", "April", "abril", "April",
		"Mayo", "May", "mayo", "May",
		"Junio", "June", "junio", "June",
		"Julio", "July", "julio", "July",
		"Agosto", "August", "agosto", "August",
		"Septiembre", "September", "septiembre", "September",
		"Octubre", "October", "octubre", "October",
		"Noviembre", "November", "noviembre", "November",
		"Diciembre", "December", "diciembre", "December",

		// Días (Título y minúscula)
		"Lunes", "Monday", "lunes", "Monday",
		"Martes", "Tuesday", "martes", "Tuesday",
		"Miércoles", "Wednesday", "miercoles", "Wednesday",
		"Jueves", "Thursday", "jueves", "Thursday",
		"Viernes", "Friday", "viernes", "Friday",
		"Sábado", "Saturday", "sabado", "Saturday",
		"Domingo", "Sunday", "domingo", "Sunday",

		// Conectores
		" de ", " ",
		" De ", " ",
	)

	resultado := replacer.Replace(s)

	return strings.TrimSpace(resultado)
}

func FetchPosterURL(title string, ctx context.Context, cfg aws.Config) string {
	if title == "" {
		return ""
	}

	client := GetTMDBClient(ctx, cfg)
	if client == nil {
		return ""
	}

	options := map[string]string{
		"language":      "es-MX",
		"include_adult": "false",
	}

	search, err := tmdbClient.GetSearchMovies(title, options)
	if err != nil || search.TotalResults == 0 {
		return ""
	}

	if search.Results[0].PosterPath != "" {
		return "https://image.tmdb.org/t/p/w500" + search.Results[0].PosterPath
	}

	return ""
}

func NowInPeru() time.Time {
	peruLoc, _ := time.LoadLocation("America/Lima")
	return time.Now().In(peruLoc)
}

func Slugify(s string) string {
	s = strings.ToLower(s)

	// Normaliza a NFD (separa las letras con tilde en la misma letra y la tilde)
	// Ejemplo: "é" -> "e" + "´"
	t := transform.Chain(norm.NFD, runes.Remove(runes.In(unicode.Mn)), norm.NFC)
	result, _, _ := transform.String(t, s)

	// Elimina lo que no sea letras o números
	re := regexp.MustCompile(`[^a-z0-9\s-]`)
	result = re.ReplaceAllString(result, "")

	result = strings.ReplaceAll(result, " ", "-")

	reMultipleDash := regexp.MustCompile(`-+`)
	result = reMultipleDash.ReplaceAllString(result, "-")

	return strings.Trim(result, "-")
}

func BuildMovie(title, location, centerSlug, centerName, sourceURL string, date time.Time, ctx context.Context, cfg aws.Config) *models.Movie {
	now := NowInPeru()

	if date.Before(now) {
		return nil
	}

	// Lógica de expiración (TIL DynamoDB)
	expiration := date.AddDate(0, 0, 1)
	midnight := time.Date(expiration.Year(), expiration.Month(), expiration.Day(), 0, 0, 1, 0, expiration.Location())

	slugTitle := Slugify(title)
	dateTitle := fmt.Sprintf("%s#%s", date.Format("2006-01-02T15:04:05"), slugTitle)

	return &models.Movie{
		Title:      title,
		Location:   location,
		Date:       date,
		DateTitle:  dateTitle,
		CenterSlug: centerSlug,
		CenterName: centerName,
		PosterURL:  FetchPosterURL(title, ctx, cfg),
		SourceURL:  sourceURL,
		CreatedAt:  now,
		ExpiresAt:  midnight.Unix(),
	}
}
