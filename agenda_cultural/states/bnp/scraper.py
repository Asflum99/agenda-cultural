from playwright.async_api import async_playwright, Page


BNP = "https://eventos.bnp.gob.pe/externo/inicio"


async def get_movies():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--disable-dev-shm-usage",
                "--disable-extensions",
                "--disable-gpu",
                "--disable-web-security",
                "--disable-features=TranslateUI",
                "--disable-ipc-flooding-protection",
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-background-timer-throttling",
                "--disable-backgrounding-occluded-windows",
                "--disable-renderer-backgrounding",
            ],
        )
        page = await browser.new_page()

        try:
            await page.goto(BNP, wait_until="load")

            await page.select_option("select#ContentPlaceHolder1_cboCategoria", "1")
            await page.locator("a#ContentPlaceHolder1_btnBuscarEventos").click()
            await page.wait_for_selector(
                "div #portfoliolist .col-lg-4", state="visible"
            )
            movies = await page.locator("div #portfoliolist .col-lg-4").count()

            movies_info: list[dict] = []

            for movie in range(movies):
                movie_info = await _get_movies_info(movie, page)
                movies_info.append(movie_info)

            return movies_info

        except Exception as e:
            print(e)
        finally:
            await browser.close()


async def _get_movies_info(movie: int, page: Page):
    try:
        movie_info = {}

        async with page.context.expect_page() as new_page_info:
            await page.locator("div #portfoliolist .col-lg-4").nth(movie).click()

        new_page = await new_page_info.value
        await new_page.wait_for_load_state("load")

        movie_info["title"] = await new_page.locator(
            "#ContentPlaceHolder1_gpCabecera h1"
        ).text_content()
        date_time_element = await new_page.locator(
            "#ContentPlaceHolder1_gpDetalleEvento p:nth-child(2)"
        ).text_content()

        date = date_time_element.strip().replace("   ", " ")

        movie_info["date"] = date

        movie_info["location"] = await new_page.locator(
            "#ContentPlaceHolder1_gpUbicacion p"
        ).text_content()

        await new_page.close()

        return movie_info

    except Exception as e:
        print(e)
