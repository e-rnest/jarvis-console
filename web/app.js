"use strict";

const services = document.querySelector("#services");
const refreshButton = document.querySelector("#refresh");
const refreshState = document.querySelector("#refresh-state");

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

function renderCard(service) {
  const card = element("article", `card ${service.key}`);
  const top = element("div", "card-top");
  top.append(
    element("h2", "", service.name),
    element("span", `badge ${service.status}`, service.status),
  );
  card.append(top, element("p", "summary", service.summary));

  if (service.key === "receipt" && service.details) {
    const details = element("dl", "details");
    addDetail(details, "Schedule", service.details.schedule_enabled ? "Enabled" : "Disabled");
    addDetail(details, "Morning brief", service.details.morning_time);
    addDetail(details, "Timezone", service.details.timezone);
    addDetail(details, "Last claimed", service.details.last_date);
    addDetail(details, "Durable state", service.details.schedule_status);
    addDetail(details, "Printing", service.details.printing ? "Busy" : "Idle");
    if (service.details.scheduler_error) {
      addDetail(details, "Scheduler error", service.details.scheduler_error, true);
    }
    card.append(details);
  } else if (service.key === "triviarom" && service.details) {
    const details = element("dl", "details");
    addDetail(details, "Playable", service.details.playable_record_count.toLocaleString());
    addDetail(details, "Archive", service.details.record_count.toLocaleString());
    addDetail(details, "Datasets", service.details.dataset_count.toLocaleString());
    card.append(details);
  }

  if (service.key === "receipt") {
    const action = element("button", "print-button", "Print Morning Brief");
    action.type = "button";
    const actionResult = element("p", "action-result");
    action.addEventListener("click", () => printMorningBrief(action, actionResult));
    card.append(action, actionResult);
  } else {
    const launch = element("a", "launch", "Launch");
    launch.href = service.launch_url;
    card.append(launch);
  }
  return card;
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

function showLoadingCards() {
  services.replaceChildren();
  for (const name of ["Receipt", "Label", "Jeopardy", "TriviaROM", "Jellyfin"]) {
    const card = element("article", "card");
    card.append(element("h2", "", name), element("p", "summary", "Checking status…"));
    services.append(card);
  }
}

async function refresh() {
  refreshButton.disabled = true;
  refreshState.textContent = "Refreshing…";
  try {
    const response = await fetch("/api/status", { cache: "no-store" });
    if (!response.ok) throw new Error(`Console returned HTTP ${response.status}`);
    const snapshot = await response.json();
    if (!Array.isArray(snapshot.services)) throw new Error("Console returned an invalid snapshot");
    services.replaceChildren(...snapshot.services.map(renderCard));
    const completed = new Date(snapshot.generated_at);
    refreshState.textContent = `Last refreshed ${completed.toLocaleString()}`;
  } catch (error) {
    refreshState.textContent = `Refresh failed: ${error.message}`;
  } finally {
    refreshButton.disabled = false;
  }
}

refreshButton.addEventListener("click", refresh);
showLoadingCards();
refresh();
