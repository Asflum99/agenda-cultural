// Paquete webapp define la aplicación web de Agenda Cultural.
//
// Proporciona un servidor HTTP con rutas para mostrar la cartelera
// de películas agrupadas por centro cultural. Lee los datos desde
// DynamoDB y los renderiza usando plantillas Go embebidas.
//
// Es agnóstico al entorno: funciona tanto como servidor local
// estándar como dentro de una función Lambda de AWS.
//
// Despliegue: este paquete NO se despliega por separado. El compilador
// de Go lo incluye en el mismo binario "bootstrap" que cmd/web/main.go.
// Cuando Lambda ejecuta bootstrap, todo este código ya está dentro.
package webapp

import (
	"bytes"
	"context"
	"errors"
	"fmt"
	"html/template"
	"io/fs"
	"net/http"
	"os"
	"path/filepath"
	"time"

	"github.com/asflum99/agenda-cultural/internal/models"
	uihtml "github.com/asflum99/agenda-cultural/ui/html"
	"github.com/aws/aws-sdk-go-v2/aws"
	"github.com/aws/aws-sdk-go-v2/feature/dynamodb/attributevalue"
	"github.com/aws/aws-sdk-go-v2/service/dynamodb"
	"github.com/go-chi/chi/v5"
	"github.com/go-chi/chi/v5/middleware"
)

var functions = template.FuncMap{
	"dict":       dict,
	"formatDate": formatDate,
}

type TemplateData struct {
	Movies     map[string][]models.Movie
	ActivePage string
}

type Application struct {
	client        *dynamodb.Client
	templateCache map[string]*template.Template
}

func New(client *dynamodb.Client) (*Application, error) {
	templateCache, err := newTemplateCache()
	if err != nil {
		return nil, fmt.Errorf("no se pudo crear el cache de plantillas: %w", err)
	}

	return &Application{
		client:        client,
		templateCache: templateCache,
	}, nil
}

func (app *Application) Routes() http.Handler {
	r := chi.NewRouter()

	r.Use(middleware.Logger)
	r.Use(middleware.Recoverer)
	r.Use(app.originVerify)
	r.Use(app.securityHeaders)

	r.Get("/", app.homeHandler)
	r.Get("/acerca-de", app.aboutHandler)

	cssServer := http.FileServer(http.FS(os.DirFS("ui/static/css")))
	r.Handle("/css/*", http.StripPrefix("/css", cssServer))

	jsServer := http.FileServer(http.FS(os.DirFS("ui/static/js")))
	r.Handle("/js/*", http.StripPrefix("/js", jsServer))

	return r
}

func (app *Application) securityHeaders(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Security-Policy",
			"default-src 'none'; "+
				"script-src 'self'; "+
				"style-src 'self'; "+
				"img-src 'self' https://image.tmdb.org https://www.themoviedb.org; "+
				"font-src 'self'; "+
				"connect-src 'self'; "+
				"base-uri 'self'; "+
				"form-action 'none'; "+
				"frame-ancestors 'none'",
		)
		w.Header().Set("X-Content-Type-Options", "nosniff")
		w.Header().Set("X-Frame-Options", "DENY")
		w.Header().Set("Referrer-Policy", "strict-origin-when-cross-origin")
		next.ServeHTTP(w, r)
	})
}

func (app *Application) originVerify(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		secret := os.Getenv("ORIGIN_VERIFY_SECRET")
		if secret != "" && r.Header.Get("X-Origin-Verify") != secret {
			http.Error(w, "Forbidden", 403)
			return
		}
		next.ServeHTTP(w, r)
	})
}

func (app *Application) homeHandler(w http.ResponseWriter, r *http.Request) {
	allMovies, err := app.getMoviesFromDynamoDB(r.Context())
	if err != nil {
		http.Error(w, "Error cargando películas", 500)
		return
	}

	grouped := make(map[string][]models.Movie)
	for _, m := range allMovies {
		grouped[m.CenterName] = append(grouped[m.CenterName], m)
	}

	data := TemplateData{
		Movies:     grouped,
		ActivePage: "home",
	}
	app.render(w, "home.html", data)
}

func (app *Application) aboutHandler(w http.ResponseWriter, r *http.Request) {
	data := TemplateData{
		ActivePage: "about",
	}
	app.render(w, "about.html", data)
}

func (app *Application) render(w http.ResponseWriter, pageName string, data any) {
	ts, ok := app.templateCache[pageName]
	if !ok {
		http.Error(w, "La página no existe", 404)
		return
	}

	buf := new(bytes.Buffer)
	err := ts.ExecuteTemplate(buf, "base.html", data)
	if err != nil {
		http.Error(w, "Error de renderizado", 500)
		return
	}
	w.Header().Set("Content-Type", "text/html; charset=utf-8")
	buf.WriteTo(w)
}

func (app *Application) getMoviesFromDynamoDB(ctx context.Context) ([]models.Movie, error) {
	tableName := os.Getenv("MOVIES_TABLE_NAME")
	if tableName == "" {
		tableName = "Movies"
	}

	var movies []models.Movie

	result, err := app.client.Scan(ctx, &dynamodb.ScanInput{
		TableName: aws.String(tableName),
	})
	if err != nil {
		return nil, fmt.Errorf("error al escanear DynamoDB: %w", err)
	}

	err = attributevalue.UnmarshalListOfMaps(result.Items, &movies)
	if err != nil {
		return nil, fmt.Errorf("error al procesar resultados: %w", err)
	}

	return movies, nil
}

func dict(values ...any) (map[string]any, error) {
	if len(values)%2 != 0 {
		return nil, errors.New("invalid dict call")
	}
	dict := make(map[string]any, len(values)/2)
	for i := 0; i < len(values); i += 2 {
		key, ok := values[i].(string)
		if !ok {
			return nil, errors.New("dict keys must be strings")
		}
		dict[key] = values[i+1]
	}
	return dict, nil
}

func formatDate(t time.Time) string {
	days := []string{"Dom", "Lun", "Mar", "Miér", "Jue", "Vie", "Sáb"}
	months := []string{"", "ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "set", "oct", "nov", "dic"}

	dayName := days[t.Weekday()]
	monthName := months[t.Month()]

	twelveHour := t.Format("3:04 PM")

	return fmt.Sprintf("%s, %d de %s - %s",
		dayName,
		t.Day(),
		monthName,
		twelveHour)
}

func newTemplateCache() (map[string]*template.Template, error) {
	cache := make(map[string]*template.Template)

	pages, err := fs.Glob(uihtml.TemplatesFS, "pages/*.html")
	if err != nil {
		return nil, err
	}

	for _, page := range pages {
		name := filepath.Base(page)

		ts, err := template.New(name).Funcs(functions).ParseFS(uihtml.TemplatesFS, "base.html")
		if err != nil {
			return nil, err
		}

		ts, err = ts.ParseFS(uihtml.TemplatesFS, "components/*.html")
		if err != nil {
			return nil, err
		}

		ts, err = ts.ParseFS(uihtml.TemplatesFS, page)
		if err != nil {
			return nil, err
		}

		cache[name] = ts
	}

	return cache, nil
}
