// Scraper Lambda es una función de AWS Lambda ejecutada diariamente por EventBridge.
// Realiza scraping concurrente de sitios web de centros culturales para obtener
// cartelera de películas, las enriquece con pósters de TMDB y las almacena en DynamoDB.
//
// Trigger: EventBridge cron (6:00 AM UTC / 1:00 AM Perú)
// Punto de entrada: HandleRequest
package main

import (
	"context"
	"errors"
	"fmt"
	"log"
	"os"
	"sync"
	"time"

	"github.com/asflum99/agenda-cultural/internal/models"
	"github.com/asflum99/agenda-cultural/internal/scraper"
	"github.com/aws/aws-lambda-go/lambda"
	"github.com/aws/aws-sdk-go-v2/aws"
	"github.com/aws/aws-sdk-go-v2/config"
	"github.com/aws/aws-sdk-go-v2/credentials"
	"github.com/aws/aws-sdk-go-v2/feature/dynamodb/attributevalue"
	"github.com/aws/aws-sdk-go-v2/service/cloudfront"
	cftypes "github.com/aws/aws-sdk-go-v2/service/cloudfront/types"
	"github.com/aws/aws-sdk-go-v2/service/dynamodb"
	"github.com/aws/aws-sdk-go-v2/service/dynamodb/types"
	"github.com/joho/godotenv"
)

var dbClient *dynamodb.Client
var awsCfg aws.Config
var cfClient *cloudfront.Client
var cfDistributionID string

func initDB(ctx context.Context) {
	endpoint := os.Getenv("DYNAMODB_ENDPOINT")

	opts := []func(*config.LoadOptions) error{
		config.WithRegion("us-east-1"),
	}

	// Usa credenciales falsas en local
	if endpoint != "" {
		opts = append(opts, config.WithCredentialsProvider(
			credentials.StaticCredentialsProvider{
				Value: aws.Credentials{
					AccessKeyID: "test", SecretAccessKey: "test",
				},
			},
		))
	}

	cfg, err := config.LoadDefaultConfig(ctx, opts...)
	if err != nil {
		log.Printf("Error cargando configuración: %v", err)
		return
	}

	awsCfg = cfg
	dbClient = dynamodb.NewFromConfig(cfg, func(o *dynamodb.Options) {
		if endpoint != "" {
			o.BaseEndpoint = aws.String(endpoint)
		}
	})

	cfDistributionID = os.Getenv("CLOUDFRONT_DISTRIBUTION_ID")
	if cfDistributionID != "" {
		cfClient = cloudfront.NewFromConfig(cfg)
	}
}

func saveToDynamoDB(ctx context.Context, movies []models.Movie) {
	for _, movie := range movies {
		item, err := attributevalue.MarshalMap(movie)
		if err != nil {
			log.Printf("Error al parsear película %s: %v", movie.Title, err)
			continue
		}

		input := &dynamodb.PutItemInput{
			TableName:           aws.String("Movies"),
			Item:                item,
			ConditionExpression: aws.String("attribute_not_exists(CenterSlug) AND attribute_not_exists(DateTitle)"),
		}

		_, err = dbClient.PutItem(ctx, input)

		if err != nil {
			var condErr *types.ConditionalCheckFailedException
			if errors.As(err, &condErr) {
				fmt.Printf("⏭️ Saltando (ya existe): %s\n", movie.Title)
				continue
			}
			log.Printf("No se pudo guardar la película %s en Dynamo: %v", movie.Title, err)
			continue
		}
		fmt.Printf("✅ Nueva película guardada: %s\n", movie.Title)
	}
}

func invalidateCloudFrontCache(ctx context.Context) {
	if cfClient == nil {
		return
	}
	_, err := cfClient.CreateInvalidation(ctx, &cloudfront.CreateInvalidationInput{
		DistributionId: aws.String(cfDistributionID),
		InvalidationBatch: &cftypes.InvalidationBatch{
			Paths: &cftypes.Paths{
				Quantity: aws.Int32(1),
				Items:    []string{"/*"},
			},
			CallerReference: aws.String(fmt.Sprintf("scraper-%d", time.Now().UnixNano())),
		},
	})
	if err != nil {
		log.Printf("⚠️ Error invalidando CloudFront: %v", err)
		return
	}
	log.Println("✅ Invalidación de CloudFront solicitada")
}

func HandleRequest(ctx context.Context) (string, error) {
	scrapers := []scraper.CulturalScraper{
		scraper.BNPScraper{},
		scraper.BritanicoScraper{},
		// TODO: LumScraper
	}

	resultsChan := make(chan []models.Movie, len(scrapers))
	var wg sync.WaitGroup

	for _, s := range scrapers {
		wg.Add(1)

		go func(s scraper.CulturalScraper) {
			defer wg.Done()

			movies, err := s.GetMovies(ctx, awsCfg)
			if err != nil {
				log.Printf("Error en %s: %v", s.Name(), err)
				return
			}
			resultsChan <- movies
		}(s)
	}

	go func() {
		wg.Wait()
		close(resultsChan)
	}()

	var allMovies []models.Movie
	for res := range resultsChan {
		allMovies = append(allMovies, res...)
	}

	saveToDynamoDB(ctx, allMovies)

	go invalidateCloudFrontCache(ctx)

	return fmt.Sprintf("Éxito: %d películas procesadas", len(allMovies)), nil
}

func main() {
	err := godotenv.Load()
	if err != nil {
		log.Println("Error cargando el archivo .env")
	}

	initDB(context.Background())

	lambda.Start(HandleRequest)
}
