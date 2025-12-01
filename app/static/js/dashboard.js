document.addEventListener("DOMContentLoaded", () => {
  const navLinks = document.querySelectorAll(".sidebar-link");
  const sections = document.querySelectorAll(".page-section");
  const topbarTitle = document.getElementById("topbarTitle");

  // Sidebar navigation click handler
  navLinks.forEach(link => {
    link.addEventListener("click", (e) => {
      e.preventDefault();

      // remove active from all links
      navLinks.forEach(l => l.classList.remove("active"));
      // set active on clicked link
      link.classList.add("active");

      // hide all sections
      const targetId = link.getAttribute("data-target");
      sections.forEach(sec => sec.classList.remove("active"));

      // show target section
      const targetSection = document.getElementById(targetId);
      if (targetSection) {
        targetSection.classList.add("active");
      }

      // update topbar title
      if (topbarTitle) {
        topbarTitle.textContent = link.innerText.trim();
      }
    });
  });

  // Upload dropzone behaviour
  const dropzone = document.getElementById("uploadDropzone");
  const fileInput = document.getElementById("uploadInput");
  const previewImg = document.getElementById("uploadPreview");
  const placeholder = document.getElementById("uploadPlaceholder");

  function handleFiles(files) {
    if (!files || files.length === 0) return;

    const file = files[0];

    // show preview
    if (previewImg) {
      const url = URL.createObjectURL(file);
      previewImg.src = url;
      previewImg.classList.remove("d-none");
    }

    // hide placeholder text
    if (placeholder) {
      placeholder.style.display = "none";
    }
  }

  if (dropzone && fileInput) {
    // click to open file dialog
    dropzone.addEventListener("click", () => fileInput.click());

    // handle file selection via dialog
    fileInput.addEventListener("change", () => {
      if (fileInput.files && fileInput.files.length > 0) {
        handleFiles(fileInput.files);
      }
    });

    // drag and drop support
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
});
