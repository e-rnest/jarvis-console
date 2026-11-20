"use strict";

const services = document.querySelector("#services");
const refreshButton = document.querySelector("#refresh");
const refreshState = document.querySelector("#refresh-state");
const consoleBuild = document.querySelector("#console-build");

function element(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function valueText(value) {
  if (value === null || value === undefined || value === "") return "None";
  if (typeof value === "boolean") return value ? "Yes" : "No";
  return String(value);
}

function addDetail(list, label, value, error = false) {
  const wrapper = element("div", `detail${error ? " error" : ""}`);
  wrapper.append(element("dt", "", label), element("dd", "", valueText(value)));
  list.append(wrapper);
}

function renderPrinters(printers) {
  const row = element("div", "printer-chips");
  if (!Array.isArray(printers)) {
    row.append(element("p", "printer-chip unknown", "Printer status unavailable"));
    return row;
  }
  for (const printer of printers) {
    const chip = element("div", `printer-chip ${printer.state}`);
    chip.append(element("strong", "printer-chip-title", `${printer.name} \u00b7 ${printer.text}`));
    if (printer.note) chip.append(element("span", "printer-chip-note", printer.note));
    const checked = printer.checked_at
      ? `Checked ${new Date(printer.checked_at).toLocaleTimeString([], { hour: "numeric", minute: "2-digit" })}`
      : "Not checked yet";
    chip.append(element("span", "printer-chip-note", checked));
    if (printer.busy) {
      chip.append(element("span", "printer-chip-note busy",
        "Busy: check skipped, showing last result"));
    }
    row.append(chip);
  }
  return row;
}

// Cards are built once from the catalog so Launch, Print and View Log work
// immediately. Health results only update the badge, summary and details.
function buildCard(service) {
  const card = element("article", `card ${service.key}`);
  card.dataset.key = service.key;
  const top = element("div", "card-top");
  top.append(element("h2", "", service.name), element("span", "badge"));
  card.append(top, element("p", "summary"), element("div", "card-status"));

  const actions = element("div", "card-actions");
  if (service.key === "ipps") {
    const viewLog = element("button", "print-button", "View Log");
    viewLog.type = "button";
    viewLog.addEventListener("click", openIppsLog);
    actions.append(viewLog);
    card.append(actions);
    return card;
  }
  if (service.key === "receipt") {
    const action = element("button", "print-button", "Print Morning Brief");
    action.type = "button";
    const actionResult = element("p", "action-result");
    action.addEventListener("click", () => printMorningBrief(action, actionResult));
    actions.append(action);
    appendSecondaryLinks(actions, service);
    card.append(actions, actionResult);
    return card;
  }
  if (service.launch_url) {
    const launch = element("a", "launch", "Launch");
    launch.href = service.launch_url;
    actions.append(launch);
  }
  appendSecondaryLinks(actions, service);
  card.append(actions);
  return card;
}

function appendSecondaryLinks(actions, service) {
  for (const link of service.secondary_links || []) {
    const secondary = element("a", "launch secondary", link.label);
    secondary.href = link.url;
    actions.append(secondary);
  }
}

function updateCard(card, service) {
  const badge = card.querySelector(".badge");
  badge.className = `badge ${service.status}`;
  badge.textContent = service.status;
  card.querySelector(".summary").textContent = service.summary;
  card.querySelector(".card-status").replaceChildren(...renderStatusDetails(service));
}

function renderStatusDetails(service) {
  const nodes = [];
  if (service.key === "receipt" && service.printers !== undefined) {
    nodes.push(renderPrinters(service.printers));
  }
  const details = element("dl", "details");
  if (service.key === "receipt" && service.details) {
    addDetail(details, "Schedule", service.details.schedule_enabled ? "Enabled" : "Disabled");
    addDetail(details, "Morning brief", service.details.morning_time);
    addDetail(details, "Timezone", service.details.timezone);
    addDetail(details, "Last claimed", service.details.last_date);
    addDetail(details, "Durable state", service.details.schedule_status);
    addDetail(details, "Printing", service.details.printing ? "Busy" : "Idle");
    if (service.details.scheduler_error) {
      addDetail(details, "Scheduler error", service.details.scheduler_error, true);
    }
  } else if (service.key === "triviarom" && service.details) {
    addDetail(details, "Playable", service.details.playable_record_count.toLocaleString());
    addDetail(details, "Archive", service.details.record_count.toLocaleString());
    addDetail(details, "Datasets", service.details.dataset_count.toLocaleString());
  } else if (service.key === "jellyfin" && service.details) {
    addDetail(details, "Server", service.details.server_name);
    addDetail(details, "Version", service.details.version);
  } else if (service.key === "semavox" && service.details) {
    addDetail(details, "Uptime", `${service.details.uptime_seconds.toLocaleString()} sec`);
    addDetail(details, "Audio", service.details.audio_ready ? "Ready" : "Unavailable");
    addDetail(details, "Volume", `${service.details.volume_percent}%`);
  }
  if (details.childElementCount) nodes.push(details);
  return nodes;
}

// Thermal Telegram has no health check of its own; it follows Receipt.
function withTelegramCard(list) {
  return list.flatMap(service => {
    if (service.key !== "receipt") return [service];
    return [service, {
      key: "ipps",
      name: "Thermal Telegram",
      status: service.status,
      summary: "Encrypted telegram delivery and persistent message history",
    }];
  });
}

function showServices(list) {
  let added = false;
  for (const service of withTelegramCard(list)) {
    let card = services.querySelector(`[data-key="${service.key}"]`);
    if (!card) {
      card = buildCard(service);
      makeDraggable(card);
      services.append(card);
      added = true;
    }
    updateCard(card, service);
  }
  if (added) applyCardOrder();
}

// Card order: desktop-only drag and drop, remembered per browser. Nothing is
// written to the server. Keys missing from the saved order (new services)
// fall back to the default rank, then catalog order.
const DEFAULT_CARD_ORDER = [
  "homeassistant", "semavox",
  "manifest", "wallboard",
  "jellyfin", "blacktorrent",
  "receipt", "ipps", "label",
];
const CARD_ORDER_KEY = "jarvis.cardOrder";
const canDrag = window.matchMedia("(hover: hover) and (pointer: fine)").matches;
const resetOrderButton = document.querySelector("#reset-order");
let draggedCard = null;

function savedCardOrder() {
  try {
    const saved = JSON.parse(localStorage.getItem(CARD_ORDER_KEY));
    return Array.isArray(saved) ? saved.filter(key => typeof key === "string") : null;
  } catch (error) {
    return null;
  }
}

function saveCardOrder() {
  const keys = [...services.children].map(card => card.dataset.key);
  try {
    localStorage.setItem(CARD_ORDER_KEY, JSON.stringify(keys));
  } catch (error) {
    // Private mode or blocked storage: the order lasts until reload.
  }
  updateResetButton();
}

function applyCardOrder() {
  const saved = savedCardOrder() || [];
  const rank = key => {
    const savedIndex = saved.indexOf(key);
    if (savedIndex !== -1) return savedIndex;
    const defaultIndex = DEFAULT_CARD_ORDER.indexOf(key);
    return saved.length + (defaultIndex !== -1 ? defaultIndex : DEFAULT_CARD_ORDER.length);
  };
  const cards = [...services.children];
  const catalogIndex = new Map(cards.map((card, index) => [card, index]));
  cards.sort((a, b) => rank(a.dataset.key) - rank(b.dataset.key)
    || catalogIndex.get(a) - catalogIndex.get(b));
  services.append(...cards);
  updateResetButton();
}

function updateResetButton() {
  if (resetOrderButton) resetOrderButton.hidden = !canDrag || !savedCardOrder();
}

function makeDraggable(card) {
  if (!canDrag) return;
  card.draggable = true;
  card.addEventListener("dragstart", event => {
    // Let links and buttons inside the card keep their own drag behaviour.
    if (event.target !== card) return;
    draggedCard = card;
    event.dataTransfer.effectAllowed = "move";
    event.dataTransfer.setData("text/plain", card.dataset.key);
    requestAnimationFrame(() => card.classList.add("dragging"));
  });
  card.addEventListener("dragend", () => {
    card.classList.remove("dragging");
    if (draggedCard) saveCardOrder();
    draggedCard = null;
  });
}

services.addEventListener("dragover", event => {
  if (!draggedCard) return;
  event.preventDefault();
  event.dataTransfer.dropEffect = "move";
  const target = event.target.closest(".card");
  if (!target || target === draggedCard) return;
  const rect = target.getBoundingClientRect();
  // Side-by-side cards split left/right; full-width cards split top/bottom.
  const fullWidth = rect.width > services.getBoundingClientRect().width * 0.75;
  const before = fullWidth
    ? event.clientY < rect.top + rect.height / 2
    : event.clientX < rect.left + rect.width / 2;
  const reference = before ? target : target.nextElementSibling;
  if (reference !== draggedCard) services.insertBefore(draggedCard, reference);
});

services.addEventListener("drop", event => {
  if (draggedCard) event.preventDefault();
});

if (resetOrderButton) {
  resetOrderButton.addEventListener("click", () => {
    try {
      localStorage.removeItem(CARD_ORDER_KEY);
    } catch (error) {
      // Nothing saved to clear.
    }
    applyCardOrder();
  });
}

async function printMorningBrief(button, output) {
  const confirmed = window.confirm(
    "Print one Morning Brief now? This will produce physical paper output.",
  );
  if (!confirmed) return;

  button.disabled = true;
  output.className = "action-result pending";
  output.textContent = "Sending one print request…";
  try {
    const response = await fetch("/api/actions/morning-brief", {
      method: "POST",
      cache: "no-store",
    });
    const result = await response.json();
    if (!result || typeof result.outcome !== "string" || typeof result.message !== "string") {
      throw new Error("Console returned an invalid action result");
    }
    output.className = `action-result ${result.outcome}`;
    output.textContent = result.message;
  } catch (error) {
    output.className = "action-result uncertain";
    output.textContent =
      "The Console response was lost. Check the physical printer before trying again.";
  } finally {
    button.disabled = false;
  }
}

const ippsDialog = document.querySelector("#ipps-log");
const ippsLogRows = document.querySelector("#ipps-log-rows");
const ippsLogState = document.querySelector("#ipps-log-state");
document.querySelector("#ipps-close").addEventListener("click", () => ippsDialog.close());

async function openIppsLog() {
  ippsLogRows.replaceChildren();
  ippsLogState.textContent = "Loading messages…";
  ippsDialog.showModal();
  try {
    const response = await fetch("/api/ipps/history", { cache: "no-store" });
    if (!response.ok) throw new Error(`History unavailable (HTTP ${response.status})`);
    const payload = await response.json();
    if (!Array.isArray(payload.messages)) throw new Error("Invalid history response");
    for (const entry of payload.messages) {
      const row = element("tr");
      for (const field of ["sender", "message", "ip", "location"]) {
        row.append(element("td", "", entry[field] || "-"));
      }
      ippsLogRows.append(row);
    }
    ippsLogState.textContent = `${payload.messages.length} most recent message(s), newest first.`;
  } catch (error) {
    ippsLogState.textContent = error.message;
  }
}

async function loadCatalog() {
  try {
    const response = await fetch("/api/services", { cache: "no-store" });
    if (!response.ok) return;
    const catalog = await response.json();
    // A status snapshot may already have built the cards; don't regress badges.
    if (Array.isArray(catalog.services) && !services.childElementCount) {
      showServices(catalog.services);
    }
  } catch (error) {
    // Cards are still built when the status snapshot arrives.
  }
}

function markStatusFailed() {
  for (const badge of services.querySelectorAll(".badge.checking")) {
    badge.className = "badge unknown";
    badge.textContent = "unknown";
    badge.closest(".card").querySelector(".summary").textContent = "Status check did not complete";
  }
}

async function refresh() {
  refreshButton.disabled = true;
  refreshState.textContent = "Checking status…";
  try {
    const response = await fetch("/api/status", { cache: "no-store" });
    if (!response.ok) throw new Error(`Console returned HTTP ${response.status}`);
    const snapshot = await response.json();
    if (!Array.isArray(snapshot.services)) throw new Error("Console returned an invalid snapshot");
    if (snapshot.console && typeof snapshot.console.version === "string"
        && typeof snapshot.console.build === "string") {
      consoleBuild.textContent = `Jarvis Console v${snapshot.console.version} · build ${snapshot.console.build}`;
    } else {
      consoleBuild.textContent = "Jarvis Console build unavailable";
    }
    showServices(snapshot.services);
    const completed = new Date(snapshot.generated_at);
    refreshState.textContent = `Last refreshed ${completed.toLocaleString()}`;
  } catch (error) {
    markStatusFailed();
    refreshState.textContent = `Refresh failed: ${error.message}`;
  } finally {
    refreshButton.disabled = false;
  }
}

refreshButton.addEventListener("click", refresh);
loadCatalog();
refresh();
