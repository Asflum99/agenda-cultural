build-MoviesScraperFunction:
	CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build \
		-ldflags="-s -w" \
		-tags lambda.norpc \
		-o $(ARTIFACTS_DIR)/bootstrap \
		./cmd/scraper

build-WebFunction:
	CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build \
		-ldflags="-s -w" \
		-o $(ARTIFACTS_DIR)/bootstrap \
		./cmd/web
