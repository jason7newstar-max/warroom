const galleries = document.querySelectorAll("[data-gallery]");

galleries.forEach((gallery) => {
  const slides = Array.from(gallery.querySelectorAll("[data-slide]"));
  const prev = gallery.querySelector("[data-prev]");
  const next = gallery.querySelector("[data-next]");
  const dots = gallery.querySelector("[data-dots]");
  let index = 0;
  let startX = 0;

  const render = () => {
    slides.forEach((slide, i) => {
      slide.hidden = i !== index;
    });
    Array.from(dots.children).forEach((dot, i) => {
      dot.setAttribute("aria-current", String(i === index));
    });
  };

  const go = (delta) => {
    index = (index + delta + slides.length) % slides.length;
    render();
  };

  slides.forEach((_, i) => {
    const dot = document.createElement("button");
    dot.type = "button";
    dot.className = "dot";
    dot.setAttribute("aria-label", `Show image ${i + 1}`);
    dot.addEventListener("click", () => {
      index = i;
      render();
    });
    dots.appendChild(dot);
  });

  prev.addEventListener("click", () => go(-1));
  next.addEventListener("click", () => go(1));

  gallery.addEventListener("touchstart", (event) => {
    startX = event.touches[0].clientX;
  }, { passive: true });

  gallery.addEventListener("touchend", (event) => {
    const endX = event.changedTouches[0].clientX;
    const diff = endX - startX;
    if (Math.abs(diff) > 42) {
      go(diff > 0 ? -1 : 1);
    }
  }, { passive: true });

  render();
});
