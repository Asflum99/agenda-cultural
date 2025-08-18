from playwright.async_api import async_playwright, Page


ALIANZA_FRANCESA = (
    "https://aflima.org.pe/eventos/?post_type=evento&categoria%5B%5D=cine"
)


async def get_movies():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        try:
            await page.goto(ALIANZA_FRANCESA, wait_until="load")

            # Grupo de secciones que proyectan películas gratuitas
            cine_locators = await page.locator(
                ".ctbtn", has_text="Ingreso libre"
            ).count()

            movies_info: list[dict] = []

            for locator in range(cine_locators):
                await _enter_movie_page(locator, page)

                movies = await page.locator(".cajas_cont_item").count()

                for movie in range(movies):
                    movie_info = await _get_movies_info(movie, page)
                    movies_info.append(movie_info)

                await page.go_back(wait_until="load")

            return movies_info

        except Exception as e:
            print(e)


async def _get_movies_info(movie: int, page: Page):
    try:
        movie_info = {}
        movie_box = page.locator(".cajas_cont_item").nth(movie)

        movie_info["title"] = await movie_box.locator(
            ".cajas_cont_item_fecha .cajas__fecha_txt"
        ).inner_text()

        blocks = await movie_box.locator(
            ".cajas_cont_item_info .cajas__info_fecha2"
        ).count()

        keys = ["date", "location"]
        for block in range(blocks):
            info = (
                (
                    await movie_box.locator(".cajas_cont_item_info .cajas__info_fecha2")
                    .nth(block)
                    .inner_text()
                )
                .replace("\n", " ")
                .strip()
            )

            movie_info[keys[block]] = info

        return movie_info
    except Exception as e:
        print(e)


async def _enter_movie_page(locator: int, page: Page):
    await page.locator(".ctbtn a.btn-outline-primary").nth(locator).click()
    await page.wait_for_load_state("load")
