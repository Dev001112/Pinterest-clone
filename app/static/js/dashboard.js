document.addEventListener("DOMContentLoaded", () => {
  const navLinks = document.querySelectorAll(".sidebar-link[data-target]");
  const sections = document.querySelectorAll(".page-section");
  const topbarTitle = document.getElementById("topbarTitle");

  // Sidebar navigation
  navLinks.forEach(link => {
    link.addEventListener("click", (e) => {
      e.preventDefault();
      navLinks.forEach(l => l.classList.remove("active"));
      link.classList.add("active");

      const targetId = link.getAttribute("data-target");
      sections.forEach(sec => sec.classList.remove("active"));
      const targetSection = document.getElementById(targetId);
      if (targetSection) {
        targetSection.classList.add("active");
      }

      if (topbarTitle) {
        topbarTitle.textContent = link.innerText.trim();
      }
    });
  });

  // Upload dropzone with preview
  const dropzone = document.getElementById("uploadDropzone");
  const fileInput = document.getElementById("uploadInput");
  const previewImg = document.getElementById("uploadPreview");
  const placeholder = document.getElementById("uploadPlaceholder");

  function handleFiles(files) {
    if (!files || files.length === 0) return;
    const file = files[0];

    if (previewImg) {
      const url = URL.createObjectURL(file);
      previewImg.src = url;
      previewImg.classList.remove("d-none");
    }
    if (placeholder) {
      placeholder.style.display = "none";
    }
  }

  if (dropzone && fileInput) {
    dropzone.addEventListener("click", () => fileInput.click());

    fileInput.addEventListener("change", () => {
      if (fileInput.files && fileInput.files.length > 0) {
        handleFiles(fileInput.files);
      }
    });

    dropzone.addEventListener("dragover", (e) => {
      e.preventDefault();
      dropzone.classList.add("dragover");
    });

    dropzone.addEventListener("dragleave", () => {
      dropzone.classList.remove("dragover");
    });

    dropzone.addEventListener("drop", (e) => {
      e.preventDefault();
      dropzone.classList.remove("dragover");
      if (e.dataTransfer.files.length > 0) {
        fileInput.files = e.dataTransfer.files;
        handleFiles(e.dataTransfer.files);
      }
    });
  }

  // Initial wiring for share / like / save
  attachShareHandlers();
  attachLikeSaveHandlers();

  // Messages tab global user search
  const msgSearch = document.getElementById("messagesSearch");
  const msgResults = document.getElementById("messagesSearchResults");

  if (msgSearch && msgResults) {
    msgSearch.addEventListener("input", async () => {
      const q = msgSearch.value.trim();
      if (!q) {
        msgResults.innerHTML = "";
        return;
      }

      try {
        const res = await fetch(`/api/search_users?q=${encodeURIComponent(q)}`);
        const data = await res.json();
        msgResults.innerHTML = "";

        data.results.forEach(u => {
          const row = document.createElement("div");
          row.textContent = u.username;
          row.className = "user-result-row";
          row.onclick = () => {
            window.location.href = `/dashboard?tab=messages&chat_with=${u.id}`;
          };
          msgResults.appendChild(row);
        });
      } catch (err) {
        console.error("messages search error", err);
      }
    });
  }

  // Live messages polling for active chat
  const chatMessages = document.getElementById("chatMessages");
  if (chatMessages) {
    const otherId = chatMessages.dataset.chatUserId;
    if (otherId) {
      startMessagesPolling(otherId, chatMessages);
    }
  }

  // Live pins polling for home feed
  const pinGrid = document.getElementById("pinGrid");
  if (pinGrid) {
    startPinsPolling(pinGrid);
  }
});

// Attach share popup & search handlers
function attachShareHandlers() {
  // buttons
  document.querySelectorAll(".share-btn").forEach(btn => {
    if (btn.dataset._shareWired) return;
    btn.dataset._shareWired = "1";

    btn.addEventListener("click", (e) => {
      e.stopPropagation();
      const pinId = btn.dataset.pin;
      const popup = document.getElementById(`sharePopup-${pinId}`);
      if (!popup) return;

      document.querySelectorAll(".share-popup").forEach(p => {
        if (p !== popup) p.classList.add("d-none");
      });

      popup.classList.toggle("d-none");
    });
  });

  // close share popups when clicking outside
  document.addEventListener("click", (e) => {
    if (!e.target.closest(".share-popup") && !e.target.closest(".share-btn")) {
      document.querySelectorAll(".share-popup").forEach(p => p.classList.add("d-none"));
    }
  });

  // user search inside share popups
  document.querySelectorAll(".user-search-input").forEach(input => {
    if (input.dataset._shareSearchWired) return;
    input.dataset._shareSearchWired = "1";

    input.addEventListener("input", async () => {
      const query = input.value.trim();
      const pinId = input.dataset.pin;
      const resultsBox = document.getElementById(`searchResults-${pinId}`);
      if (!resultsBox) return;

      if (!query) {
        resultsBox.innerHTML = "";
        return;
      }

      try {
        const res = await fetch(`/api/search_users?q=${encodeURIComponent(query)}`);
        const data = await res.json();
        resultsBox.innerHTML = "";

        data.results.forEach(u => {
          const row = document.createElement("div");
          row.textContent = u.username;
          row.className = "user-result-row";
          row.onclick = () => sendPinToUser(pinId, u.id, u.username);
          resultsBox.appendChild(row);
        });
      } catch (err) {
        console.error("user search error", err);
      }
    });
  });
}

// Attach like / save handlers
function attachLikeSaveHandlers() {
  // LIKE
  document.querySelectorAll(".like-btn").forEach(btn => {
    if (btn.dataset._likeWired) return;
    btn.dataset._likeWired = "1";

    btn.addEventListener("click", async () => {
      const pinId = btn.dataset.pin;
      try {
        const res = await fetch(`/pin/${pinId}/like`, {
          method: "POST",
          headers: {
            "X-Requested-With": "XMLHttpRequest"
          }
        });
        const data = await res.json();
        if (!data.ok) return;

        const countSpan = btn.querySelector(".like-count");
        const iconSpan = btn.querySelector(".like-icon");

        if (data.liked) {
          btn.classList.add("active");
          if (iconSpan) iconSpan.textContent = "♥";
        } else {
          btn.classList.remove("active");
          if (iconSpan) iconSpan.textContent = "♡";
        }
        if (countSpan) countSpan.textContent = data.count;
      } catch (err) {
        console.error("like error", err);
      }
    });
  });

  // SAVE
  document.querySelectorAll(".save-btn").forEach(btn => {
    if (btn.dataset._saveWired) return;
    btn.dataset._saveWired = "1";

    btn.addEventListener("click", async () => {
      const pinId = btn.dataset.pin;
      try {
        const res = await fetch(`/pin/${pinId}/save`, {
          method: "POST",
          headers: {
            "X-Requested-With": "XMLHttpRequest"
          }
        });
        const data = await res.json();
        if (!data.ok) return;

        const iconSpan = btn.querySelector(".save-icon");

        if (data.saved) {
          btn.classList.add("active");
          if (iconSpan) iconSpan.textContent = "🔖 Saved";
        } else {
          btn.classList.remove("active");
          if (iconSpan) iconSpan.textContent = "🔖 Save";
        }
      } catch (err) {
        console.error("save error", err);
      }
    });
  });
}

// send pin via AJAX – stay on home, show toast
async function sendPinToUser(pinId, userId, username) {
  try {
    const form = new FormData();
    form.append("pin_id", pinId);
    form.append("recipient_id", userId);
    form.append("text", "");

    const res = await fetch("/messages/send", {
      method: "POST",
      body: form,
      headers: {
        "X-Requested-With": "XMLHttpRequest"
      }
    });

    const data = await res.json();
    if (data.ok) {
      showToast(`Pin shared with ${username}`);
      document.querySelectorAll(".share-popup").forEach(p => p.classList.add("d-none"));
    } else {
      showToast(data.error || "Could not share pin", true);
    }
  } catch (err) {
    console.error("sendPinToUser error", err);
    showToast("Failed to share pin", true);
  }
}

// small toast similar to flash message
function showToast(message, isError = false) {
  const containerId = "pinboard-toast-container";
  let container = document.getElementById(containerId);
  if (!container) {
    container = document.createElement("div");
    container.id = containerId;
    container.style.position = "fixed";
    container.style.top = "16px";
    container.style.right = "16px";
    container.style.zIndex = "9999";
    document.body.appendChild(container);
  }

  const alert = document.createElement("div");
  alert.className = `alert alert-${isError ? "danger" : "success"} alert-dismissible fade show`;
  alert.role = "alert";
  alert.textContent = message;

  const btn = document.createElement("button");
  btn.type = "button";
  btn.className = "btn-close";
  btn.setAttribute("data-bs-dismiss", "alert");
  btn.onclick = () => alert.remove();

  alert.appendChild(btn);
  container.appendChild(alert);

  setTimeout(() => {
    alert.classList.remove("show");
    setTimeout(() => alert.remove(), 150);
  }, 3000);
}

// polling: keep DM updated without manual refresh
function startMessagesPolling(otherId, container) {
  let lastJson = null;

  async function fetchAndRender() {
    try {
      const res = await fetch(`/api/messages_for/${otherId}`);
      const data = await res.json();
      const jsonString = JSON.stringify(data.messages);
      if (jsonString === lastJson) {
        return;
      }
      lastJson = jsonString;

      container.innerHTML = "";
      data.messages.forEach(m => {
        const wrapper = document.createElement("div");
        wrapper.className = "mb-2";

        const who = m.from_me ? "You" : data.other_username;
        let inner = `<strong>${who}:</strong> `;
        if (m.text) {
          inner += m.text;
        }
        if (m.pin) {
          inner += `
            <div class="mt-1 p-2 border rounded small">
              <div class="fw-semibold mb-1">Shared pin:</div>
              <div class="d-flex align-items-center gap-2">
                <img src="${m.pin.image_url}"
                     alt="${m.pin.title}"
                     class="shared-pin-thumb">
                <div>
                  <div class="fw-semibold text-truncate">${m.pin.title}</div>
                  ${m.pin.description ? `<small class="text-muted d-block text-truncate">${m.pin.description}</small>` : ""}
                </div>
              </div>
            </div>
          `;
        }

        wrapper.innerHTML = inner;
        container.appendChild(wrapper);
      });

      container.scrollTop = container.scrollHeight;
    } catch (err) {
      console.error("poll messages error", err);
    }
  }

  fetchAndRender();
  setInterval(fetchAndRender, 3000);
}

// polling: keep Home feed pins updated
function startPinsPolling(container) {
  let lastJson = null;

  async function fetchAndRenderPins() {
    try {
      const res = await fetch("/api/pins");
      const data = await res.json();
      const jsonString = JSON.stringify(data.pins);
      if (jsonString === lastJson) return;
      lastJson = jsonString;

      container.innerHTML = "";
      data.pins.forEach(pin => {
        const card = document.createElement("div");
        card.className = "pin-card";
        card.innerHTML = `
          <img src="${pin.image_url}"
               class="pin-card-img" alt="${pin.title}">
          <div class="pin-card-body">
            <div class="fw-semibold text-truncate">${pin.title}</div>
            ${pin.description ? `<small class="text-muted d-block text-truncate">${pin.description}</small>` : ""}
            <small class="text-muted d-block">
              by ${pin.author} · ${pin.created_at}
            </small>

            <div class="d-flex gap-2 mt-2 align-items-center flex-wrap">

              <button type="button"
                      class="btn btn-sm btn-outline-danger like-btn ${pin.liked ? "active" : ""}"
                      data-pin="${pin.id}">
                <span class="like-icon">${pin.liked ? "♥" : "♡"}</span>
                <span class="like-count">${pin.likes_count}</span>
              </button>

              <button type="button"
                      class="btn btn-sm btn-outline-secondary save-btn ${pin.saved ? "active" : ""}"
                      data-pin="${pin.id}">
                <span class="save-icon">${pin.saved ? "🔖 Saved" : "🔖 Save"}</span>
              </button>

              <button class="btn btn-sm btn-outline-secondary share-btn"
                      type="button"
                      data-pin="${pin.id}">
                <span class="icon">📤</span> Share
              </button>
            </div>

            <div class="share-popup d-none" id="sharePopup-${pin.id}">
              <div class="share-popup-inner">
                <input type="text"
                       class="form-control form-control-sm user-search-input"
                       placeholder="Search user..."
                       data-pin="${pin.id}">
                <div class="user-search-results mt-2"
                     id="searchResults-${pin.id}"></div>
              </div>
            </div>
          </div>
        `;
        container.appendChild(card);
      });

      attachShareHandlers();
      attachLikeSaveHandlers();
    } catch (err) {
      console.error("poll pins error", err);
    }
  }

  fetchAndRenderPins();
  setInterval(fetchAndRenderPins, 5000);
}
