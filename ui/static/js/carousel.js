(function () {
  function initCarousel(wrapper) {
    if (wrapper.dataset.carouselInitialized) return;
    wrapper.dataset.carouselInitialized = "true";

    const carousel = wrapper.querySelector(".movie-carousel");
    const btnLeft = wrapper.querySelector(".carousel-btn-left");
    const btnRight = wrapper.querySelector(".carousel-btn-right");
    const fadeLeft = wrapper.querySelector(".carousel-fade-left");
    const fadeRight = wrapper.querySelector(".carousel-fade-right");

    if (!carousel) return;

    const scrollAmount = 320;

    function updateButtons() {
      const { scrollLeft, scrollWidth, clientWidth } = carousel;
      const canScrollLeft = scrollLeft > 5;
      const canScrollRight = scrollLeft < scrollWidth - clientWidth - 5;

      btnLeft.style.display = canScrollLeft ? "flex" : "none";
      btnRight.style.display = canScrollRight ? "flex" : "none";

      fadeLeft.classList.toggle("visible", canScrollLeft);
      fadeRight.classList.toggle("visible", canScrollRight);
    }

    btnLeft.addEventListener("click", () => {
      carousel.scrollBy({ left: -scrollAmount, behavior: "smooth" });
    });

    btnRight.addEventListener("click", () => {
      carousel.scrollBy({ left: scrollAmount, behavior: "smooth" });
    });

    carousel.addEventListener("scroll", updateButtons, { passive: true });
    window.addEventListener("resize", updateButtons);

    updateButtons();
  }

  function initAllCarousels() {
    document.querySelectorAll(".carousel-wrapper").forEach(initCarousel);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initAllCarousels);
  } else {
    initAllCarousels();
  }

  if (typeof htmx !== "undefined") {
    document.body.addEventListener("htmx:afterSettle", initAllCarousels);
    document.body.addEventListener("htmx:afterSwap", initAllCarousels);
  }
})();
