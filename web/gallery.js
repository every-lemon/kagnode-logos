(() => {
  "use strict";
  const embedded = JSON.parse(document.querySelector("#catalog").textContent);
  let catalog = embedded;
  let query = "";
  let limit = 48;
  const filters = { family: "", color: "", format: "" };
  const grid = document.querySelector("#grid");
  const notice = document.querySelector("#status");
  const dialog = document.querySelector("#asset-dialog");
  let current = null;
  const rawRoot =
    "https://raw.githubusercontent.com/every-lemon/kagnode-logos/";
  const assetUrl = (item) =>
    rawRoot +
    catalog.source_commit +
    "/" +
    item.path.split("/").map(encodeURIComponent).join("/");
  const element = (tag, text, className) => {
    const node = document.createElement(tag);
    if (text) node.textContent = text;
    if (className) node.className = className;
    return node;
  };
  const toast = (text) => {
    const node = document.querySelector("#toast");
    node.textContent = text;
    node.hidden = false;
    clearTimeout(toast.timer);
    toast.timer = setTimeout(() => {
      node.hidden = true;
    }, 3500);
  };
  function preview(item, interactive = false) {
    const box = element(interactive ? "button" : "div", "", "preview");
    if (interactive) {
      box.type = "button";
      box.setAttribute("aria-label", "View " + item.name);
      box.addEventListener("click", () => open(item));
    }
    if (["svg", "png", "webp"].includes(item.format)) {
      const image = element("img");
      image.src = assetUrl(item);
      image.alt = item.name;
      image.loading = "lazy";
      image.addEventListener("error", () => {
        image.remove();
        box.append(
          element(
            "span",
            item.format.toUpperCase() + " · preview unavailable",
            "file-icon",
          ),
        );
      });
      box.append(image);
    } else box.append(element("span", item.format.toUpperCase(), "file-icon"));
    return box;
  }
  async function download(item, button) {
    const old = button.textContent;
    button.textContent = "Downloading…";
    button.disabled = true;
    try {
      const response = await fetch(assetUrl(item), {
        credentials: "omit",
        signal: AbortSignal.timeout(30000),
      });
      if (!response.ok) throw Error("Download failed");
      const bytes = await response.arrayBuffer();
      if (crypto.subtle) {
        const hash = Array.from(
          new Uint8Array(await crypto.subtle.digest("SHA-256", bytes)),
          (n) => n.toString(16).padStart(2, "0"),
        ).join("");
        if (hash !== item.sha256) throw Error("Artwork checksum mismatch");
      }
      const link = element("a");
      link.href = URL.createObjectURL(new Blob([bytes]));
      link.download = item.path.split("/").pop();
      document.body.append(link);
      link.click();
      link.remove();
      setTimeout(() => URL.revokeObjectURL(link.href), 10000);
      toast("Downloaded " + item.name);
    } catch (error) {
      toast(
        "Download unavailable. Check your connection or use “Open original”.",
      );
    } finally {
      button.textContent = old;
      button.disabled = false;
    }
  }
  function card(item) {
    const article = element("article", "", "asset");
    article.append(preview(item, true));
    const info = element("div", "", "asset-info");
    info.append(element("h2", item.name, "asset-title"));
    const meta = element("div", "", "meta");
    meta.append(
      element("span", item.format.toUpperCase() + " · " + item.color),
      element(
        "span",
        item.width ? item.width + " × " + item.height : item.family,
      ),
    );
    info.append(meta);
    const actions = element("div", "", "asset-actions");
    const get = element("button", "Download");
    get.type = "button";
    get.addEventListener("click", () => download(item, get));
    const details = element("button", "Details");
    details.type = "button";
    details.addEventListener("click", () => open(item));
    actions.append(get, details);
    info.append(actions);
    article.append(info);
    return article;
  }
  function open(item) {
    current = item;
    dialog.querySelector("h2").textContent = item.name;
    dialog.querySelector("#dialog-preview").replaceChildren(preview(item));
    const details = dialog.querySelector("dl");
    details.replaceChildren();
    for (const [key, value] of Object.entries({
      Format: item.format.toUpperCase(),
      Family: item.family,
      Variant: item.variant,
      Dimensions: item.width
        ? item.width + " × " + item.height
        : "Vector / document",
      Path: item.path,
      SHA256: item.sha256,
    }))
      details.append(element("dt", key), element("dd", value));
    document.querySelector("#original").href = assetUrl(item);
    if (!dialog.open) dialog.showModal();
  }
  function render() {
    const result = catalog.assets.filter(
      (item) =>
        (!query ||
          (item.name + " " + item.path + " " + item.family + " " + item.variant)
            .toLowerCase()
            .includes(query)) &&
        Object.entries(filters).every(
          ([key, value]) => !value || item[key] === value,
        ),
    );
    grid.replaceChildren(...result.slice(0, limit).map(card));
    document.querySelector("#count").textContent =
      result.length.toLocaleString() +
      " assets" +
      (result.length > limit ? " · showing " + limit : "");
    document.querySelector("#more").hidden = result.length <= limit;
    document.querySelector("#empty").hidden = result.length !== 0;
    document.querySelector("#revision").textContent =
      "Artwork " + catalog.source_commit.slice(0, 7);
  }
  function menus() {
    for (const key of Object.keys(filters)) {
      const menu = document.querySelector('[data-menu="' + key + '"]');
      menu.replaceChildren();
      for (const value of [
        "",
        ...new Set(catalog.assets.map((a) => a[key])),
      ].sort()) {
        const button = element("button", value || "All " + key + "s");
        button.type = "button";
        button.setAttribute("aria-pressed", String(filters[key] === value));
        button.addEventListener("click", () => {
          filters[key] = value;
          limit = 48;
          menu.closest("details").open = false;
          menus();
          render();
        });
        menu.append(button);
      }
      document.querySelector('[data-label="' + key + '"]').textContent =
        filters[key] || key.charAt(0).toUpperCase() + key.slice(1);
    }
  }
  async function refresh(manual = false) {
    const button = document.querySelector("#refresh");
    button.disabled = true;
    try {
      const response = await fetch(rawRoot + "main/catalog.json", {
        credentials: "omit",
        cache: "no-cache",
        signal: AbortSignal.timeout(12000),
      });
      if (!response.ok) throw Error("Catalog unavailable");
      const next = await response.json();
      if (
        next.schema !== 1 ||
        !/^[a-f0-9]{40}$/.test(next.source_commit) ||
        !Array.isArray(next.assets) ||
        next.assets.length > 10000 ||
        next.assets.some(
          (a) =>
            !/^[\w./-]+$/.test(a.path) ||
            a.path.includes("..") ||
            !/^[a-f0-9]{64}$/.test(a.sha256),
        )
      )
        throw Error("Invalid catalog");
      catalog = next;
      notice.hidden = true;
      menus();
      render();
      if (manual) toast("Catalog refreshed");
    } catch (error) {
      notice.hidden = false;
      notice.textContent =
        "GitHub could not be reached. Showing the included catalog. Artwork and downloads still need an internet connection. Use Refresh to try again.";
    } finally {
      button.disabled = false;
    }
  }
  document
    .querySelector("#viewer-download")
    .addEventListener("click", (event) => {
      event.preventDefault();
      const clone = document.documentElement.cloneNode(true);
      clone.querySelector("#grid").replaceChildren();
      clone
        .querySelectorAll("dialog,details")
        .forEach((node) => node.removeAttribute("open"));
      clone
        .querySelectorAll(
          "[data-kn-scroll-rail],.kn-scroll-rail,.kn-scroll-preference",
        )
        .forEach((node) => node.remove());
      const link = element("a");
      link.href = URL.createObjectURL(
        new Blob(["<!doctype html>\n" + clone.outerHTML], {
          type: "text/html",
        }),
      );
      link.download = "kagnode-logos.html";
      document.body.append(link);
      link.click();
      link.remove();
      setTimeout(() => URL.revokeObjectURL(link.href), 10000);
    });
  document.querySelector("#search").addEventListener("input", (event) => {
    query = event.target.value.trim().toLowerCase();
    limit = 48;
    render();
  });
  document.querySelector("#reset").addEventListener("click", () => {
    Object.keys(filters).forEach((key) => {
      filters[key] = "";
    });
    query = "";
    limit = 48;
    document.querySelector("#search").value = "";
    menus();
    render();
  });
  document.querySelector("#more").addEventListener("click", () => {
    limit += 48;
    render();
  });
  document
    .querySelector("#refresh")
    .addEventListener("click", () => refresh(true));
  document
    .querySelector("#close-dialog")
    .addEventListener("click", () => dialog.close());
  document
    .querySelector("#download-current")
    .addEventListener("click", (event) => download(current, event.target));
  document.querySelector("#copy-url").addEventListener("click", async () => {
    try {
      await navigator.clipboard.writeText(assetUrl(current));
      toast("URL copied");
    } catch {
      toast("Use Open original to copy the URL from your browser.");
    }
  });
  document.querySelectorAll("[data-background]").forEach((button) =>
    button.addEventListener("click", () => {
      document.body.dataset.preview = button.dataset.background;
      document
        .querySelectorAll("[data-background]")
        .forEach((b) => b.setAttribute("aria-pressed", String(b === button)));
    }),
  );
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape")
      document.querySelectorAll("details").forEach((d) => {
        d.open = false;
      });
  });
  document.addEventListener("click", (event) =>
    document.querySelectorAll("details[open]").forEach((d) => {
      if (!d.contains(event.target)) d.open = false;
    }),
  );
  menus();
  render();
  refresh();
})();
