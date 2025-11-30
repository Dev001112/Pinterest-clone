// Sidebar navigation
document.addEventListener("DOMContentLoaded", () => {
  const navLinks = document.querySelectorAll(".sidebar-link");
  const sections = document.querySelectorAll(".page-section");
  const topbarTitle = document.getElementById("topbarTitle");

  navLinks.forEach(link => {
    link.addEventListener("click", (e) => {
      e.preventDefault();

      // active sidebar
      navLinks.forEach(l => l.classList.remove("active"));
      link.classList.add("active");

      // sections
      const targetId = link.getAttribute("data-target");
      sections.forEach(sec => sec.classList.remove("active"));
      document.getElementById(targetId).classList.add("active");

      // update title
      topbarTitle.textContent = link.innerText.trim();
    });
  });

  // Upload dropzone
  const dropzone = document.getElementById("uploadDropzone");
  const fileInput = document.getElementById("uploadInput");

  if (dropzone && fileInput) {
    dropzone.addEventListener("click", () => fileInput.click());

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
        // later: show preview or send to backend
      }
    });
  }
});
