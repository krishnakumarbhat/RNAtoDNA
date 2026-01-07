(() => {
  const MAX_UPLOAD_BYTES = 4 * 1024 * 1024; // 4MB

  const uploadArea = document.getElementById("upload-area");
  const fileInput = document.getElementById("file-input");
  const fileName = document.getElementById("file-name");
  const convertBtn = document.getElementById("convert-btn");
  const downloadBtn = document.getElementById("download-btn");
  const previewBtn = document.getElementById("preview-btn");
  const previewEl = document.getElementById("preview");
  const statsEl = document.getElementById("stats");
  const alertEl = document.getElementById("alert");

  const removeO2Prime = document.getElementById("remove_o2prime");
  const h5ToC7 = document.getElementById("h5_to_c7");

  /** @type {File|null} */
  let selectedFile = null;
  /** @type {string|null} */
  let convertedText = null;

  const RNA_TO_DNA = {
    A: "DA",
    C: "DC",
    G: "DG",
    U: "DT",
    ADE: "DA",
    CYT: "DC",
    GUA: "DG",
    URA: "DT",
  };

  function showAlert(type, message) {
    alertEl.className = `alert-custom ${type}`;
    alertEl.style.display = "flex";
    alertEl.innerHTML = `${type === "success" ? '<i class="bi bi-check-circle-fill"></i>' : '<i class="bi bi-exclamation-circle-fill"></i>'}${escapeHtml(message)}`;
  }

  function hideAlert() {
    alertEl.style.display = "none";
    alertEl.textContent = "";
  }

  function escapeHtml(str) {
    return String(str)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }

  function setFile(file) {
    hideAlert();
    convertedText = null;
    downloadBtn.style.display = "none";
    previewBtn.style.display = "none";
    previewEl.style.display = "none";
    statsEl.style.display = "none";

    if (!file) {
      selectedFile = null;
      fileName.style.display = "none";
      convertBtn.disabled = true;
      return;
    }

    if (!file.name.toLowerCase().endsWith(".pdb")) {
      showAlert("error", "Invalid file format. Only .pdb files are allowed.");
      return;
    }

    if (file.size > MAX_UPLOAD_BYTES) {
      showAlert("error", `File too large. Max size is ${MAX_UPLOAD_BYTES / (1024 * 1024)}MB.`);
      return;
    }

    selectedFile = file;
    fileName.textContent = file.name;
    fileName.style.display = "inline-block";
    convertBtn.disabled = false;
    uploadArea.classList.add("dragover");
  }

  function convert(text, options) {
    const lines = text.split(/\r?\n/);
    /** stats */
    const stats = {
      lines_in: lines.length,
      lines_out: 0,
      atoms_converted: 0,
      residues_converted: 0,
      o2prime_removed: 0,
      h5_renamed: 0,
    };

    const seenResidues = new Set();
    const out = [];

    for (const rawLine of lines) {
      let line = rawLine;

      if (line.startsWith("ATOM")) {
        const residueName = line.slice(17, 20).trim();
        const mapped = RNA_TO_DNA[residueName];
        if (mapped) {
          line = line.slice(0, 17) + ` ${mapped} ` + line.slice(21);
          stats.atoms_converted += 1;

          const chainId = line.slice(21, 22);
          const resSeq = line.slice(22, 26);
          const iCode = line.slice(26, 27);
          const key = `${chainId}|${resSeq}|${iCode}`;
          if (!seenResidues.has(key)) {
            seenResidues.add(key);
            stats.residues_converted += 1;
          }
        }

        const atomName = line.slice(12, 16).trim();
        if (options.remove_o2prime && atomName === "O2'") {
          stats.o2prime_removed += 1;
          continue;
        }

        if (options.h5_to_c7 && atomName === "H5") {
          line = line.slice(0, 12) + " C7 " + line.slice(16);
          stats.h5_renamed += 1;
        }
      }

      out.push(line);
    }

    stats.lines_out = out.length;
    return { text: out.join("\n") + "\n", stats };
  }

  function downloadText(filename, text) {
    const blob = new Blob([text], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    downloadBtn.href = url;
    downloadBtn.download = filename;
    downloadBtn.style.display = "flex";

    // revoke later
    setTimeout(() => URL.revokeObjectURL(url), 30_000);
  }

  // Click to upload
  uploadArea.addEventListener("click", () => fileInput.click());
  uploadArea.addEventListener("keydown", (e) => {
    if (e.key === "Enter" || e.key === " ") fileInput.click();
  });

  // File selected
  fileInput.addEventListener("change", (e) => {
    const file = e.target.files && e.target.files[0];
    setFile(file || null);
  });

  // Drag and drop
  uploadArea.addEventListener("dragover", (e) => {
    e.preventDefault();
    uploadArea.classList.add("dragover");
  });

  uploadArea.addEventListener("dragleave", () => {
    if (!fileInput.files.length) uploadArea.classList.remove("dragover");
  });

  uploadArea.addEventListener("drop", (e) => {
    e.preventDefault();
    const files = e.dataTransfer.files;
    setFile(files && files[0] ? files[0] : null);
  });

  convertBtn.addEventListener("click", async () => {
    hideAlert();

    if (!selectedFile) {
      showAlert("error", "Please choose a .pdb file.");
      return;
    }

    convertBtn.disabled = true;
    convertBtn.innerHTML = '<i class="bi bi-hourglass-split"></i> Converting...';

    try {
      const text = await selectedFile.text();
      const options = {
        remove_o2prime: removeO2Prime.checked,
        h5_to_c7: h5ToC7.checked,
      };

      const result = convert(text, options);
      convertedText = result.text;

      const base = selectedFile.name.replace(/\.pdb$/i, "");
      const outName = `converted_DNA_from_${base}.pdb`;
      downloadText(outName, convertedText);

      statsEl.style.display = "block";
      statsEl.innerHTML = `
        <div style="font-weight: 600;">Conversion summary</div>
        <div style="color: rgba(255,255,255,0.7); font-size: 0.95rem;">
          Lines: ${result.stats.lines_in} → ${result.stats.lines_out} · Atoms converted: ${result.stats.atoms_converted} · Residues converted: ${result.stats.residues_converted} · O2' removed: ${result.stats.o2prime_removed} · H5 renamed: ${result.stats.h5_renamed}
        </div>
      `;

      previewBtn.style.display = "block";
      showAlert("success", "Conversion successful. Download is ready.");
    } catch (err) {
      showAlert("error", err && err.message ? err.message : "Conversion failed.");
    } finally {
      convertBtn.disabled = false;
      convertBtn.innerHTML = '<i class="bi bi-arrow-repeat"></i> Convert to DNA';
    }
  });

  previewBtn.addEventListener("click", () => {
    if (!convertedText) return;
    const lines = convertedText.split(/\r?\n/).slice(0, 200);
    previewEl.style.display = "block";
    previewEl.innerHTML = `<pre style="color: rgba(255,255,255,0.9); margin:0; font-size:0.9rem;">${escapeHtml(lines.join("\n"))}</pre>`;
    previewEl.scrollTop = 0;
  });
})();
