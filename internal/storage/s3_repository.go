package storage

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"

	"github.com/asflum99/agenda-cultural/internal/models"
	"github.com/aws/aws-sdk-go-v2/aws"
	"github.com/aws/aws-sdk-go-v2/service/s3"
)

type S3Repository struct {
	S3Client   *s3.Client
	BucketName string
	Key        string
}

func (r *S3Repository) SaveMovies(ctx context.Context, movies []models.Movie) error {
	jsonData, err := json.MarshalIndent(movies, "", "  ")
	if err != nil {
		return fmt.Errorf("error serializando películas a JSON: %w", err)
	}

	_, err = r.S3Client.PutObject(ctx, &s3.PutObjectInput{
		Bucket:      aws.String(r.BucketName),
		Key:         aws.String(r.Key),
		Body:        bytes.NewReader(jsonData),
		ContentType: aws.String("application/json"),
	})

	if err != nil {
		return fmt.Errorf("error subiendo archivo a S3: %w", err)
	}

	return nil
}
