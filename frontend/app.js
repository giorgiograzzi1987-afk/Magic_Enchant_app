const state = {
  spells: [],
  filters: {
    q: "",
    level: "",
    class: "",
    school: "",
    ritual: "",
    concentration: "",
    component: "",
  },
  character: {
    name: "",
    class_name: "",
    subclass: "",
    level: 1,
  },
};

const pgNameInput = document.getElementById("pgName");
const pgSubclassInput = document.getElementById("pgSubclass");
const pgLevelSelect = document.getElementById("pgLevel");
const pgClassSelect = document.getElementById("pgClass");
const savePgButton = document.getElementById("savePg");
const spellsList = document.getElementById("spellsList");
const knownList = document.getElementById("knownList");
const slotsPanel = document.getElementById("slotsPanel");
const pgSection = document.getElementById("pgSection");
const spellsSection = document.getElementById("spellsSection");
const showPgButton = document.getElementById("showPg");
const showSpellsButton = document.getElementById("showSpells");

const filterInputs = {
  searchInput: document.getElementById("searchInput"),
  levelFilter: document.getElementById("levelFilter"),
  classFilter: document.getElementById("classFilter"),
  schoolFilter: document.getElementById("schoolFilter"),
  ritualFilter: document.getElementById("ritualFilter"),
  concentrationFilter: document.getElementById("concentrationFilter"),
  componentFilter: document.getElementById("componentFilter"),
};

const advancedPanel = document.getElementById("advancedFilters");
const toggleAdvanced = document.getElementById("toggleAdvanced");

toggleAdvanced.addEventListener("click", () => {
  advancedPanel.classList.toggle("hidden");
});

function setActivePage(page) {
  const isPg = page === "pg";
  pgSection.classList.toggle("hidden", !isPg);
  spellsSection.classList.toggle("hidden", isPg);
  showPgButton.classList.toggle("active", isPg);
  showSpellsButton.classList.toggle("active", !isPg);
}

showPgButton.addEventListener("click", () => setActivePage("pg"));
showSpellsButton.addEventListener("click", () => setActivePage("spells"));

function buildLevelOptions() {
  for (let i = 1; i <= 20; i += 1) {
    const opt = document.createElement("option");
    opt.value = i;
    opt.textContent = `${i}`;
    pgLevelSelect.appendChild(opt);
  }
}

function serializeFilters() {
  const params = new URLSearchParams();
  Object.entries(state.filters).forEach(([key, value]) => {
    if (value !== "" && value !== null && value !== undefined) {
      params.append(key, value);
    }
  });
  return params.toString();
}

async function fetchSpells() {
  const query = serializeFilters();
  const res = await fetch(`/api/spells?${query}`);
  state.spells = await res.json();
  renderSpells();
  renderKnown();
}

async function fetchCharacter() {
  const res = await fetch("/api/character");
  state.character = await res.json();
  pgNameInput.value = state.character.name || "";
  pgSubclassInput.value = state.character.subclass || "";
  pgClassSelect.value = state.character.class_name || "";
  pgLevelSelect.value = state.character.level || 1;
  renderSlots();
}

async function updateCharacter() {
  state.character.name = pgNameInput.value.trim();
  state.character.subclass = pgSubclassInput.value.trim();
  state.character.class_name = pgClassSelect.value || "";
  state.character.level = Number(pgLevelSelect.value || 1);
  await fetch("/api/character", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(state.character),
  });
  renderSlots();
}

function tag(label) {
  const span = document.createElement("span");
  span.className = "tag";
  span.textContent = label;
  return span;
}

function spellLevelLabel(level) {
  if (level === 0) return "Trucchetto";
  return `${level}°`;
}

function toggleButton(label, className, active) {
  const btn = document.createElement("button");
  btn.className = `toggle ${className} ${active ? "active" : ""}`;
  btn.innerHTML = `<span>${label}</span>`;
  return btn;
}

function renderSpells() {
  spellsList.innerHTML = "";
  state.spells.forEach((spell) => {
    const card = document.createElement("article");
    card.className = "card";

    const title = document.createElement("h4");
    title.textContent = spell.name;

    const meta = document.createElement("div");
    meta.className = "meta";
    meta.textContent = `${spellLevelLabel(spell.level)} · ${spell.school || ""}`;

    const classes = document.createElement("div");
    classes.className = "meta";
    classes.textContent = `Classi: ${spell.classes || "—"}`;

    const desc = document.createElement("p");
    desc.className = "description";
    desc.textContent = spell.description || "";

    const actions = document.createElement("div");
    actions.className = "actions";

    const knownBtn = toggleButton("Conosciuto", "known", spell.known);
    const preparedBtn = toggleButton("Preparato", "prepared", spell.prepared);
    const favBtn = toggleButton("Preferito", "favorite", spell.favorite);

    knownBtn.addEventListener("click", () => {
      spell.known = !spell.known;
      updateStatus(spell);
    });
    preparedBtn.addEventListener("click", () => {
      spell.prepared = !spell.prepared;
      updateStatus(spell);
    });
    favBtn.addEventListener("click", () => {
      spell.favorite = !spell.favorite;
      updateStatus(spell);
    });

    actions.append(knownBtn, preparedBtn, favBtn);

    card.append(title, meta, classes, desc, actions);
    spellsList.appendChild(card);
  });
}

function renderKnown() {
  knownList.innerHTML = "";
  state.spells
    .filter((spell) => spell.known)
    .forEach((spell) => {
      const li = document.createElement("li");
      li.innerHTML = `<span>${spell.name}</span>`;
      const tags = document.createElement("span");
      tags.className = "tags";
      tags.textContent = `${spellLevelLabel(spell.level)} · ${spell.school || ""}`;
      li.appendChild(tags);
      knownList.appendChild(li);
    });
}

async function updateStatus(spell) {
  await fetch("/api/status", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      spell_id: spell.id,
      known: spell.known,
      prepared: spell.prepared,
      favorite: spell.favorite,
    }),
  });
  fetchSpells();
}

const fullCasterSlots = {
  1: [2],
  2: [3],
  3: [4, 2],
  4: [4, 3],
  5: [4, 3, 2],
  6: [4, 3, 3],
  7: [4, 3, 3, 1],
  8: [4, 3, 3, 2],
  9: [4, 3, 3, 3, 1],
  10: [4, 3, 3, 3, 2],
  11: [4, 3, 3, 3, 2, 1],
  12: [4, 3, 3, 3, 2, 1],
  13: [4, 3, 3, 3, 2, 1, 1],
  14: [4, 3, 3, 3, 2, 1, 1],
  15: [4, 3, 3, 3, 2, 1, 1, 1],
  16: [4, 3, 3, 3, 2, 1, 1, 1],
  17: [4, 3, 3, 3, 3, 1, 1, 1, 1],
  18: [4, 3, 3, 3, 3, 1, 1, 1, 1],
  19: [4, 3, 3, 3, 3, 2, 1, 1, 1],
  20: [4, 3, 3, 3, 3, 2, 2, 1, 1],
};

const halfCasterSlots = {
  1: [0],
  2: [2],
  3: [3],
  4: [3],
  5: [4, 2],
  6: [4, 2],
  7: [4, 3],
  8: [4, 3],
  9: [4, 3, 2],
  10: [4, 3, 2],
  11: [4, 3, 3],
  12: [4, 3, 3],
  13: [4, 3, 3, 1],
  14: [4, 3, 3, 1],
  15: [4, 3, 3, 2],
  16: [4, 3, 3, 2],
  17: [4, 3, 3, 3, 1],
  18: [4, 3, 3, 3, 1],
  19: [4, 3, 3, 3, 2],
  20: [4, 3, 3, 3, 2],
};

const warlockSlots = {
  1: [1],
  2: [2],
  3: [2],
  4: [2],
  5: [2],
  6: [2],
  7: [2],
  8: [2],
  9: [2],
  10: [2],
  11: [3],
  12: [3],
  13: [3],
  14: [3],
  15: [3],
  16: [3],
  17: [4],
  18: [4],
  19: [4],
  20: [4],
};

const classProgression = {
  bardo: { type: "full", slots: fullCasterSlots },
  chierico: { type: "full", slots: fullCasterSlots },
  druido: { type: "full", slots: fullCasterSlots },
  mago: { type: "full", slots: fullCasterSlots },
  stregone: { type: "full", slots: fullCasterSlots },
  artefice: { type: "half", slots: halfCasterSlots },
  paladino: { type: "half", slots: halfCasterSlots },
  ranger: { type: "half", slots: halfCasterSlots },
  warlock: { type: "warlock", slots: warlockSlots },
};

function renderSlots() {
  slotsPanel.innerHTML = "";
  const className = state.character.class_name;
  const level = state.character.level || 1;
  const progression = classProgression[className];

  if (!progression) {
    slotsPanel.innerHTML = "<p class=\"meta\">Nessuno slot disponibile per questa classe.</p>";
    return;
  }

  const slots = progression.slots[level] || [];

  if (progression.type === "warlock") {
    const row = document.createElement("div");
    row.className = "slot-row";
    row.innerHTML = `<strong>Pact Slots</strong><span>Livello slot: ${Math.min(
      5,
      Math.ceil(level / 2)
    )}</span>`;
    const boxes = document.createElement("div");
    boxes.className = "boxes";
    for (let i = 0; i < slots[0]; i += 1) {
      const cb = document.createElement("input");
      cb.type = "checkbox";
      boxes.appendChild(cb);
    }
    row.appendChild(boxes);
    slotsPanel.appendChild(row);
    return;
  }

  for (let i = 0; i < 9; i += 1) {
    const count = slots[i] || 0;
    const row = document.createElement("div");
    row.className = "slot-row";
    row.innerHTML = `<strong>Slot ${i + 1}°</strong>`;
    const boxes = document.createElement("div");
    boxes.className = "boxes";
    for (let j = 0; j < count; j += 1) {
      const cb = document.createElement("input");
      cb.type = "checkbox";
      boxes.appendChild(cb);
    }
    row.appendChild(boxes);
    slotsPanel.appendChild(row);
  }
}

function bindFilters() {
  filterInputs.searchInput.addEventListener("input", (e) => {
    state.filters.q = e.target.value;
    debounceFetch();
  });
  filterInputs.levelFilter.addEventListener("change", (e) => {
    state.filters.level = e.target.value;
    fetchSpells();
  });
  filterInputs.classFilter.addEventListener("change", (e) => {
    state.filters.class = e.target.value;
    fetchSpells();
  });
  filterInputs.schoolFilter.addEventListener("change", (e) => {
    state.filters.school = e.target.value;
    fetchSpells();
  });
  filterInputs.ritualFilter.addEventListener("change", (e) => {
    state.filters.ritual = e.target.value;
    fetchSpells();
  });
  filterInputs.concentrationFilter.addEventListener("change", (e) => {
    state.filters.concentration = e.target.value;
    fetchSpells();
  });
  filterInputs.componentFilter.addEventListener("change", (e) => {
    state.filters.component = e.target.value;
    fetchSpells();
  });

  pgClassSelect.addEventListener("change", updateCharacter);
  pgLevelSelect.addEventListener("change", updateCharacter);
  pgNameInput.addEventListener("input", debounceSaveCharacter);
  pgSubclassInput.addEventListener("input", debounceSaveCharacter);
  savePgButton.addEventListener("click", updateCharacter);
}

let debounceId = null;
function debounceFetch() {
  clearTimeout(debounceId);
  debounceId = setTimeout(fetchSpells, 300);
}

let debounceCharacterId = null;
function debounceSaveCharacter() {
  clearTimeout(debounceCharacterId);
  debounceCharacterId = setTimeout(updateCharacter, 400);
}

buildLevelOptions();
bindFilters();
fetchCharacter();
fetchSpells();
