"use strict";
document.documentElement.classList.add("js");
const menu = document.querySelector(".menu-toggle");
const nav = document.getElementById("nav-links");
function closeMenu() {
  menu.setAttribute("aria-expanded", "false");
  nav.classList.remove("is-open");
}
menu.addEventListener("click", () => {
  const open = menu.getAttribute("aria-expanded") !== "true";
  menu.setAttribute("aria-expanded", String(open));
  nav.classList.toggle("is-open", open);
});
nav.addEventListener("click", (event) => {
  if (event.target.closest("a")) closeMenu();
});
document.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && menu.getAttribute("aria-expanded") === "true") {
    closeMenu();
    menu.focus();
  }
});
const tabs = [...document.querySelectorAll('[role="tab"]')];
function selectTab(tab, focus = false) {
  tabs.forEach((item) => {
    const selected = item === tab;
    item.setAttribute("aria-selected", String(selected));
    item.tabIndex = selected ? 0 : -1;
    document.getElementById(item.getAttribute("aria-controls")).hidden =
      !selected;
  });
  if (focus) tab.focus();
}
tabs.forEach((tab, index) => {
  tab.addEventListener("click", () => selectTab(tab));
  tab.addEventListener("keydown", (event) => {
    let next;
    if (event.key === "ArrowRight") next = (index + 1) % tabs.length;
    if (event.key === "ArrowLeft")
      next = (index + tabs.length - 1) % tabs.length;
    if (event.key === "Home") next = 0;
    if (event.key === "End") next = tabs.length - 1;
    if (next !== undefined) {
      event.preventDefault();
      selectTab(tabs[next], true);
    }
  });
});
const feedback = document.createElement("span");
feedback.setAttribute("role", "status");
feedback.setAttribute("aria-live", "polite");
feedback.style.cssText =
  "position:absolute;width:1px;height:1px;overflow:hidden;clip-path:inset(50%)";
document.body.appendChild(feedback);
document.querySelectorAll("pre").forEach((pre) => {
  const code = pre.querySelector("code");
  if (!code) return;
  const button = document.createElement("button");
  button.className = "copy";
  button.type = "button";
  button.textContent = "Copy";
  button.setAttribute(
    "aria-label",
    "Copy " + (pre.closest(".first-prompt") ? "project prompt" : "commands"),
  );
  pre.appendChild(button);
  button.addEventListener("click", async () => {
    try {
      await navigator.clipboard.writeText(code.textContent);
      button.textContent = "Copied ✓";
      feedback.textContent = "Copied to clipboard.";
    } catch {
      const range = document.createRange();
      range.selectNodeContents(code);
      const selection = window.getSelection();
      selection.removeAllRanges();
      selection.addRange(range);
      button.textContent = "Text selected";
      feedback.textContent =
        "Text selected. Press Control C or Command C to copy.";
    }
    setTimeout(() => {
      button.textContent = "Copy";
      feedback.textContent = "";
    }, 2500);
  });
});
const search = document.getElementById("command-search");
const rows = [...document.querySelectorAll("#command-table tbody tr")];
const count = document.getElementById("command-count");
search.addEventListener("input", () => {
  const query = search.value.trim().toLowerCase();
  let found = 0;
  rows.forEach((row) => {
    row.hidden = !row.textContent.toLowerCase().includes(query);
    if (!row.hidden) found++;
  });
  count.textContent = query
    ? found
      ? `${found} matching command ${found === 1 ? "group" : "groups"}`
      : "No commands found. Try a different word or clear your search."
    : `${rows.length} command groups`;
});
count.textContent = `${rows.length} command groups`;
if ("IntersectionObserver" in window) {
  const links = [...nav.querySelectorAll('a[href^="#"]')];
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        links.forEach((link) => {
          if (link.hash === "#" + entry.target.id)
            link.setAttribute("aria-current", "location");
          else link.removeAttribute("aria-current");
        });
      });
    },
    { rootMargin: "-15% 0px -65% 0px", threshold: 0 },
  );
  document
    .querySelectorAll("main section")
    .forEach((section) => observer.observe(section));
}
