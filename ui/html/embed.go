package html

import "embed"

//go:embed base.html components pages
var TemplatesFS embed.FS
