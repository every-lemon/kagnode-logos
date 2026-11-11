(() => {
  "use strict";
  const embedded = JSON.parse(document.querySelector("#catalog").textContent);
  let catalog = embedded,
    query = "",
    family = "",
    limit = 24,
    current = null;
  const filters = { color: "", format: "", product: "" };
  const grid = document.querySelector("#grid"),
    notice = document.querySelector("#status"),
    dialog = document.querySelector("#asset-dialog");
  const rawRoot =
    "https://raw.githubusercontent.com/every-lemon/kagnode-logos/";
  const families = {
    "": "All assets",
    symbols: "Symbols",
    wordmarks: "Wordmarks",
    products: "Product logos",
    icons: "App icons",
    terminal: "Terminal",
    sheets: "Logo sheets",
  };
  const colors = {
    blue: "Blue",
    black: "Black",
    white: "White",
    gray: "Gray",
    "light-gray": "Light gray",
    "light-blue": "Light blue",
    charcoal: "Charcoal",
    slate: "Slate",
    dark: "For dark backgrounds",
    light: "For light backgrounds",
    original: "Original",
  };
  const products = {
    cli: "CLI",
    cloud: "Cloud",
    developer: "Developer",
    "http-boot": "HTTP Boot",
    mail: "Mail",
    project: "Project",
    vpn: "VPN",
  };
  const formatOrder = [
    "svg",
    "png",
    "webp",
    "pdf",
    "eps",
    "ico",
    "icns",
    "txt",
    "ansi",
  ];
  const blobCache = new Map();
  const assetUrl = (path) =>
    rawRoot +
    catalog.source_commit +
    "/" +
    path.split("/").map(encodeURIComponent).join("/");
  const element = (tag, text, className) => {
    const node = document.createElement(tag);
    if (text) node.textContent = text;
    if (className) node.className = className;
    return node;
  };
  const titleCase = (value) => value.replace(/\b\w/g, (c) => c.toUpperCase());
  function title(item) {
    if (item.family === "icons") return "KagNode app icon";
    if (item.path.startsWith("symbols/"))
      return titleCase(item.variant.replace("-", " ")) + " symbol";
    if (item.family === "symbols") return "KagNode symbol";
    if (item.family === "wordmarks") return "KagNode wordmark";
    if (item.family === "sheets") return "Logo sheet";
    if (item.family === "products")
      return "KagNode " + (products[item.product] || titleCase(item.product));
    return titleCase(
      item.name
        .replace(/kagnode/gi, "KagNode")
        .replace(/\bblocks\b/g, "block lettering"),
    );
  }
  function label(key, value) {
    return key === "color"
      ? colors[value] || value
      : key === "product"
        ? products[value] || titleCase(value)
        : value.toUpperCase();
  }
  function toast(text) {
    const node = document.querySelector("#toast");
    node.textContent = text;
    node.hidden = false;
    clearTimeout(toast.timer);
    toast.timer = setTimeout(() => {
      node.hidden = true;
    }, 5000);
  }
  const hashBytes = async (bytes) =>
    Array.from(
      new Uint8Array(await crypto.subtle.digest("SHA-256", bytes)),
      (n) => n.toString(16).padStart(2, "0"),
    ).join("");
  async function fetchBytes(path, sha) {
    const response = await fetch(assetUrl(path), {
      credentials: "omit",
      signal: AbortSignal.timeout(20000),
    });
    if (!response.ok) throw Error("File unavailable");
    const bytes = await response.arrayBuffer();
    if (crypto.subtle && (await hashBytes(bytes)) !== sha)
      throw Error("File checksum mismatch");
    return bytes;
  }
  async function previewUrl(item) {
    const key = catalog.source_commit + "/" + item.preview_path;
    if (!blobCache.has(key)) {
      const task = fetchBytes(item.preview_path, item.preview_sha256).then(
        (bytes) =>
          URL.createObjectURL(
            new Blob([bytes], {
              type: {
                svg: "image/svg+xml",
                png: "image/png",
                webp: "image/webp",
                ico: "image/x-icon",
              }[item.preview_format],
            }),
          ),
      );
      blobCache.set(key, task);
      task.catch(() => blobCache.delete(key));
    }
    return blobCache.get(key);
  }
  const observer = new IntersectionObserver(
    (entries) =>
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          observer.unobserve(entry.target);
          entry.target.loadArtwork?.();
        }
      }),
    { rootMargin: "180px" },
  );
  const fitText = new ResizeObserver((entries) =>
    entries.forEach(({ target }) => {
      const pre = target.querySelector("pre");
      if (!pre) return;
      const lines = pre.textContent.split("\n"),
        columns = Math.max(...lines.map((l) => Array.from(l).length), 1);
      const size = Math.min(
        12,
        (target.clientWidth - 30) / (columns * 0.61),
        (target.clientHeight - 30) / (lines.length * 1.12),
      );
      target.style.setProperty("--ascii-size", Math.max(1, size) + "px");
    }),
  );
  function preview(item, interactive = false, files = []) {
    const box = element(
      interactive ? "button" : "div",
      "",
      "preview is-" +
        (item.family === "symbols" || item.family === "icons"
          ? "symbol"
          : item.family === "sheets"
            ? "sheet"
            : "wordmark"),
    );
    box.dataset.canvas = item.preview_background;
    if (interactive) {
      box.type = "button";
      box.setAttribute("aria-label", "View downloads for " + title(item));
      box.addEventListener("click", () => open(item, files));
    }
    if (item.preview_text) {
      box.append(element("pre", item.preview_text));
      fitText.observe(box);
    } else {
      box.classList.add("pending");
      box.loadArtwork = async () => {
        box.querySelector(".preview-error")?.remove();
        box.classList.add("pending");
        try {
          const image = element("img");
          image.alt = title(item);
          image.style.colorScheme = item.preview_background;
          image.decoding = "async";
          image.src = await previewUrl(item);
          await new Promise((resolve, reject) => {
            image.onload = resolve;
            image.onerror = reject;
            if (image.complete) image.naturalWidth ? resolve() : reject();
          });
          box.replaceChildren(image);
        } catch {
          const error = element(
            "span",
            "Preview unavailable. Check your connection.",
            "preview-error",
          );
          // No buttons nested inside the card's preview button.
          if (!interactive) {
            const retry = element("button", "Retry preview");
            retry.type = "button";
            retry.addEventListener("click", () => box.loadArtwork());
            error.append(retry);
          } else
            box.setAttribute(
              "aria-label",
              "Preview unavailable. Open downloads for " + title(item),
            );
          box.replaceChildren(error);
        } finally {
          box.classList.remove("pending");
        }
      };
      if (interactive) observer.observe(box);
      else box.loadArtwork();
    }
    return box;
  }
  function resetObservers() {
    observer.disconnect();
    fitText.disconnect();
    if (dialog.open) {
      const p = dialog.querySelector(".preview");
      if (p?.querySelector("pre")) fitText.observe(p);
    }
  }
  function groups(assets) {
    const result = new Map();
    for (const item of assets) {
      if (!result.has(item.design)) result.set(item.design, []);
      result.get(item.design).push(item);
    }
    return [...result.values()].sort(
      (a, b) =>
        Object.keys(families).indexOf(a[0].family) -
          Object.keys(families).indexOf(b[0].family) ||
        a[0].design.localeCompare(b[0].design),
    );
  }
  function preferred(files) {
    return [...files].sort(
      (a, b) =>
        formatOrder.indexOf(a.format) - formatOrder.indexOf(b.format) ||
        (b.width || 0) - (a.width || 0),
    )[0];
  }
  function card(files) {
    // Legacy download paths can contain identical copies of the same size.
    files = [
      ...new Map(
        files.map((file) => [file.format + file.sha256, file]),
      ).values(),
    ];
    const item = preferred(files),
      article = element("article", "", "asset");
    article.dataset.design = item.design;
    article.append(preview(item, true, files));
    const info = element("div", "", "asset-info");
    info.append(element("h3", title(item), "asset-title"));
    info.append(
      element(
        "p",
        item.family === "terminal"
          ? "Terminal artwork · " +
              files.length +
              " file" +
              (files.length === 1 ? "" : "s")
          : (colors[item.color] || item.color) +
              " · " +
              files.length +
              " file" +
              (files.length === 1 ? "" : "s"),
        "asset-description",
      ),
    );
    const bottom = element("div", "", "asset-bottom"),
      badges = element("div", "", "format-badges");
    const formats = [...new Set(files.map((f) => f.format))].sort(
      (a, b) => formatOrder.indexOf(a) - formatOrder.indexOf(b),
    );
    formats
      .slice(0, 4)
      .forEach((f) => badges.append(element("span", f.toUpperCase())));
    if (formats.length > 4)
      badges.append(element("span", "+" + (formats.length - 4)));
    const actions = element("div", "", "asset-actions"),
      view = element("button", "Download ↗");
    view.type = "button";
    view.setAttribute(
      "aria-label",
      "Download " + title(item) + ", " + (colors[item.color] || item.color),
    );
    view.addEventListener("click", () => open(item, files));
    actions.append(view);
    bottom.append(badges, actions);
    info.append(bottom);
    article.append(info);
    return article;
  }
  async function download(item, button) {
    const old = button.textContent;
    button.textContent = "Saving…";
    button.disabled = true;
    try {
      const bytes = await fetchBytes(item.path, item.sha256),
        url = URL.createObjectURL(new Blob([bytes])),
        link = element("a");
      link.href = url;
      link.download = item.path.split("/").pop();
      document.body.append(link);
      link.click();
      link.remove();
      setTimeout(() => URL.revokeObjectURL(url), 10000);
      toast("Downloaded " + item.path.split("/").pop());
    } catch {
      toast(
        "Download failed. Check your connection, or use View source in file details.",
      );
    } finally {
      button.textContent = old;
      button.disabled = false;
    }
  }
  function details(item) {
    current = item;
    const dl = dialog.querySelector("dl");
    dl.replaceChildren();
    for (const [key, value] of Object.entries({
      Format: item.format.toUpperCase(),
      Size: item.width
        ? item.width + " × " + item.height
        : item.family === "terminal"
          ? "Plain text artwork"
          : "Scalable vector / print",
      Path: item.path,
      SHA256: item.sha256,
    }))
      dl.append(element("dt", key), element("dd", value));
    document.querySelector("#original").href =
      "https://github.com/every-lemon/kagnode-logos/blob/" +
      catalog.source_commit +
      "/" +
      item.path;
    dialog
      .querySelectorAll(".file-row")
      .forEach((r) =>
        r.setAttribute("aria-current", String(r.dataset.path === item.path)),
      );
  }
  function open(item, files) {
    dialog.querySelector("h2").textContent = title(item);
    document.querySelector("#asset-family").textContent = families[item.family];
    document.querySelector("#asset-subtitle").textContent =
      (colors[item.color] || item.color) +
      (item.variant !== "standard"
        ? " · " + titleCase(item.variant.replace("-", " "))
        : "");
    document.querySelector("#dialog-preview").replaceChildren(preview(item));
    document.querySelector("#file-count").textContent =
      files.length + " original files";
    const options = document.querySelector("#file-options");
    options.replaceChildren();
    const sorted = [...files].sort(
      (a, b) =>
        formatOrder.indexOf(a.format) - formatOrder.indexOf(b.format) ||
        (b.width || 0) - (a.width || 0),
    );
    sorted.forEach((file) => {
      const row = element("div", "", "file-row");
      row.dataset.path = file.path;
      const meta = element("div", "", "file-info"),
        descriptor = file.width
          ? file.width + " × " + file.height
          : ["txt", "ansi"].includes(file.format)
            ? file.format === "ansi"
              ? "Colored terminal artwork"
              : "Plain text artwork"
            : "Scalable / print";
      meta.append(
        element("strong", descriptor),
        element(
          "span",
          file.size < 1024
            ? file.size + " B"
            : file.size < 1024 * 1024
              ? (file.size / 1024).toFixed(1) + " KB"
              : (file.size / 1048576).toFixed(1) + " MB",
        ),
      );
      const get = element("button", "Download");
      get.type = "button";
      get.setAttribute(
        "aria-label",
        "Download " + file.format.toUpperCase() + " " + descriptor,
      );
      get.addEventListener("click", () => {
        details(file);
        download(file, get);
      });
      row.append(
        element("span", file.format.toUpperCase(), "file-format"),
        meta,
        get,
      );
      options.append(row);
    });
    details(item);
    dialog.querySelector(".file-details").open = false;
    if (!dialog.open) dialog.showModal();
    options.scrollTop = 0;
  }
  function render() {
    resetObservers();
    const terms = query.split(/\s+/).filter(Boolean);
    const result = catalog.assets.filter(
      (item) =>
        (!family || item.family === family) &&
        terms.every((term) =>
          (
            title(item) +
            " " +
            item.path +
            " " +
            item.family +
            " " +
            item.variant +
            " " +
            item.color
          )
            .toLowerCase()
            .includes(term),
        ) &&
        Object.entries(filters).every(
          ([key, value]) => !value || item[key] === value,
        ),
    );
    const designs = groups(result);
    grid.replaceChildren(...designs.slice(0, limit).map(card));
    document.querySelector("#count").textContent =
      designs.length + " designs · " + result.length + " files";
    document.querySelector("#category-title").textContent = families[family];
    document.querySelector("#design-total").textContent = groups(
      catalog.assets,
    ).length;
    document.querySelector("#file-total").textContent = catalog.assets.length;
    document.querySelector("#more").hidden = designs.length <= limit;
    document.querySelector("#empty").hidden = designs.length > 0;
    document.querySelector("#reset").hidden =
      !query && !Object.values(filters).some(Boolean);
    document.querySelector("#revision").textContent =
      "Source " + catalog.source_commit.slice(0, 7);
    document
      .querySelectorAll("[data-family]")
      .forEach((b) =>
        b.setAttribute("aria-pressed", String(b.dataset.family === family)),
      );
  }
  function menus() {
    const host = document.querySelector("#families");
    host.replaceChildren();
    const icons = {
      "": "grid",
      symbols: "layers",
      wordmarks: "plan",
      products: "compute",
      icons: "grid",
      terminal: "code",
      sheets: "images",
    };
    for (const [key, name] of Object.entries(families)) {
      const count = groups(
        catalog.assets.filter((a) => !key || a.family === key),
      ).length;
      const b = element("button");
      b.type = "button";
      b.dataset.family = key;
      b.setAttribute("aria-pressed", String(family === key));
      b.innerHTML = KagNodeCore.icon(icons[key]);
      b.append(
        element("span", name),
        element("span", String(count), "category-count"),
      );
      b.addEventListener("click", () => {
        family = key;
        limit = 24;
        render();
      });
      host.append(b);
    }
    for (const key of Object.keys(filters)) {
      const menu = document.querySelector('[data-menu="' + key + '"]');
      menu.replaceChildren();
      for (const value of [
        "",
        ...new Set(catalog.assets.map((a) => a[key]).filter(Boolean)),
      ]) {
        const button = element(
          "button",
          value ? label(key, value) : "All " + key + "s",
        );
        button.type = "button";
        button.setAttribute("aria-pressed", String(filters[key] === value));
        button.addEventListener("click", () => {
          filters[key] = value;
          limit = 24;
          const details = menu.closest("details");
          details.open = false;
          menus();
          render();
          details.querySelector("summary").focus();
        });
        menu.append(button);
      }
      document.querySelector('[data-label="' + key + '"]').textContent =
        filters[key] ? label(key, filters[key]) : titleCase(key);
    }
  }
  function validate(next) {
    if (
      next.schema !== 2 ||
      !/^[a-f0-9]{40}$/.test(next.source_commit) ||
      !Array.isArray(next.assets) ||
      !next.assets.length ||
      next.assets.length > 10000
    )
      throw Error("Invalid catalog");
    const safe = (path) =>
      typeof path === "string" &&
      /^[\w./-]+$/.test(path) &&
      !path.startsWith("/") &&
      !path.split("/").includes("..");
    if (
      next.assets.some(
        (a) =>
          !safe(a.path) ||
          !/^[a-f0-9]{64}$/.test(a.sha256) ||
          !families[a.family] ||
          typeof a.design !== "string" ||
          ![...formatOrder].includes(a.format) ||
          (a.preview_text
            ? typeof a.preview_text !== "string" ||
              a.preview_text.length > 24000 ||
              /\x1b/.test(a.preview_text)
            : !safe(a.preview_path) ||
              !["svg", "png", "webp", "ico"].includes(a.preview_format) ||
              !/^[a-f0-9]{64}$/.test(a.preview_sha256)),
      )
    )
      throw Error("Invalid catalog assets");
  }
  async function refresh(manual = false) {
    const button = document.querySelector("#refresh");
    button.disabled = true;
    const spinner = window.KagNodeLoading.spinner();
    spinner.style.setProperty("--kn-spinner-size", "22px");
    button.prepend(spinner);
    button.setAttribute("aria-busy", "true");
    try {
      const response = await fetch(rawRoot + "main/catalog.json", {
        credentials: "omit",
        cache: "no-cache",
        signal: AbortSignal.timeout(12000),
      });
      if (!response.ok) throw Error("Catalog unavailable");
      const next = await response.json();
      validate(next);
      catalog = next;
      notice.hidden = true;
      if (!dialog.open) {
        menus();
        render();
      }
      if (manual) toast("Catalog is up to date");
    } catch {
      notice.hidden = false;
      notice.textContent =
        "Using the included catalog. GitHub could not be reached; artwork and downloads need internet access. Use Refresh to retry.";
    } finally {
      spinner.remove();
      button.removeAttribute("aria-busy");
      button.disabled = false;
    }
  }
  const reset = () => {
    Object.keys(filters).forEach((k) => {
      filters[k] = "";
    });
    query = "";
    limit = 24;
    document.querySelector("#search").value = "";
    menus();
    render();
  };
  document
    .querySelector("#viewer-download")
    .addEventListener("click", (event) => {
      event.preventDefault();
      const clone = document.documentElement.cloneNode(true);
      clone.querySelector("#grid").replaceChildren();
      clone.querySelector("#families").replaceChildren();
      clone.querySelector("#file-options").replaceChildren();
      clone.querySelector("#dialog-preview").replaceChildren();
      clone.querySelector("#toast").hidden = true;
      clone.querySelector("#catalog").textContent = JSON.stringify(
        catalog,
      ).replace(/</g, "\\u003c");
      clone.querySelector("#search").value = "";
      clone
        .querySelectorAll("dialog,details")
        .forEach((n) => n.removeAttribute("open"));
      clone
        .querySelectorAll(
          ".kn-scroll-rail,.kn-scroll-preference,.kn-scroll-settings",
        )
        .forEach((n) => n.remove());
      clone
        .querySelectorAll(".kn-scroll-root,.kn-scroll-region")
        .forEach((n) =>
          n.classList.remove("kn-scroll-root", "kn-scroll-region"),
        );
      const link = element("a"),
        url = URL.createObjectURL(
          new Blob(["<!doctype html>\n" + clone.outerHTML], {
            type: "text/html",
          }),
        );
      link.href = url;
      link.download = "kagnode-logos.html";
      document.body.append(link);
      link.click();
      link.remove();
      setTimeout(() => URL.revokeObjectURL(url), 10000);
    });
  document.querySelector("#search").addEventListener("input", (e) => {
    query = e.target.value.trim().toLowerCase();
    limit = 24;
    render();
  });
  document.querySelector("#reset").addEventListener("click", reset);
  document.querySelector("#empty-reset").addEventListener("click", reset);
  document.querySelector("#more").addEventListener("click", () => {
    limit += 24;
    render();
  });
  document
    .querySelector("#refresh")
    .addEventListener("click", () => refresh(true));
  document
    .querySelector("#close-dialog")
    .addEventListener("click", () => dialog.close());
  dialog.addEventListener("click", (e) => {
    if (e.target === dialog) {
      const r = dialog.getBoundingClientRect();
      if (
        e.clientX < r.left ||
        e.clientX > r.right ||
        e.clientY < r.top ||
        e.clientY > r.bottom
      )
        dialog.close();
    }
  });
  document.querySelector("#copy-url").addEventListener("click", async () => {
    try {
      await navigator.clipboard.writeText(assetUrl(current.path));
      toast("File link copied");
    } catch {
      toast("Use View source to copy the file address.");
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
  document.querySelector("#viewer-settings").addEventListener("click", () => {
    document.querySelector("#scroll-preference").value =
      window.KagNodeScroll.mode;
    window.KagNodeControls?.sync();
    document.querySelector("#viewer-preferences").showModal();
  });
  document
    .querySelector("#scroll-preference")
    .addEventListener("change", (e) =>
      window.KagNodeScroll.setMode(e.target.value),
    );
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape")
      document.querySelectorAll(".filter-set details[open]").forEach((d) => {
        d.open = false;
        d.querySelector("summary").focus();
      });
    if (
      e.key === "/" &&
      !dialog.open &&
      !e.ctrlKey &&
      !e.metaKey &&
      !e.altKey &&
      !/INPUT|TEXTAREA/.test(document.activeElement.tagName)
    ) {
      e.preventDefault();
      document.querySelector("#search").focus();
    }
    if (e.key === "ArrowDown" && e.target.matches(".filter-set summary")) {
      e.preventDefault();
      e.target.parentElement.open = true;
      e.target.parentElement.querySelector("button")?.focus();
    }
  });
  document.addEventListener("click", (e) =>
    document.querySelectorAll(".filter-set details[open]").forEach((d) => {
      if (!d.contains(e.target)) d.open = false;
    }),
  );
  document.addEventListener(
    "toggle",
    (e) => {
      if (e.target.matches?.(".filter-set details[open]"))
        document.querySelectorAll(".filter-set details[open]").forEach((d) => {
          if (d !== e.target) d.open = false;
        });
    },
    true,
  );
  validate(embedded);
  menus();
  render();
  refresh();
})();
