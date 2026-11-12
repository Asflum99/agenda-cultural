// Web es el punto de entrada del servidor HTTP de Agenda Cultural.
// Se ejecuta en dos modos según el entorno:
//
//   - Local: servidor HTTP estándar en localhost:8080 (go run ./cmd/web/)
//   - Producción: función Lambda adaptada con aws-lambda-go-api-proxy,
//     invocada por CloudFront a través de una Lambda Function URL privada.
//
// Inicializa el cliente de DynamoDB y delega el enrutamiento y
// renderizado al paquete internal/webapp.
package main

import (
	"context"
	"log"
	"net/http"
	"os"

	"github.com/asflum99/agenda-cultural/internal/webapp"
	"github.com/aws/aws-lambda-go/lambda"
	"github.com/aws/aws-sdk-go-v2/config"
	"github.com/aws/aws-sdk-go-v2/service/dynamodb"
	"github.com/awslabs/aws-lambda-go-api-proxy/httpadapter"
)

func main() {
	cfg, err := config.LoadDefaultConfig(context.Background(), config.WithRegion(os.Getenv("AWS_REGION")))
	if err != nil {
		log.Fatal(err)
	}

	client := dynamodb.NewFromConfig(cfg, func(o *dynamodb.Options) {
		// DYNAMODB_ENDPOINT solo existe en local, no en producción
		if endpoint := os.Getenv("DYNAMODB_ENDPOINT"); endpoint != "" {
			o.BaseEndpoint = &endpoint
		}
	})

	app, err := webapp.New(client)
	if err != nil {
		log.Fatal(err)
	}

	if os.Getenv("AWS_LAMBDA_RUNTIME_API") != "" {
		adapter := httpadapter.NewV2(app.Routes())
		lambda.Start(adapter.ProxyWithContext)
	} else {
		log.Println("Servidor corriendo en http://localhost:8080")
		log.Fatal(http.ListenAndServe(":8080", app.Routes()))
	}
}
