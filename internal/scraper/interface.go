package scraper

import (
	"context"

	"github.com/asflum99/agenda-cultural/internal/models"
	"github.com/aws/aws-sdk-go-v2/aws"
)

type CulturalScraper interface {
	Name() string
	GetMovies(ctx context.Context, cfg aws.Config) ([]models.Movie, error)
}
