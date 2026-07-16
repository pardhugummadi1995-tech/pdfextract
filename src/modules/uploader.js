/**
 * Uploader module.
 *
 * Wires up drag-and-drop, click-to-browse and (read) progress reporting for a
 * PDF file, then hands the selected file back to the caller as an ArrayBuffer.
 * Browser-only.
 */

export function createUploader({ dropzone, fileInput, browseButton, onFile, onError }) {
  function reject(message) {
    if (onError) onError(message);
  }

  async function handleFile(file) {
    if (!file) return;
    if (file.type !== "application/pdf" && !file.name.toLowerCase().endsWith(".pdf")) {
      reject(`"${file.name}" is not a PDF file.`);
      return;
    }
    const arrayBuffer = await readAsArrayBuffer(file);
    onFile({ file, arrayBuffer });
  }

  function readAsArrayBuffer(file) {
    return new Promise((resolve, reject2) => {
      const reader = new FileReader();
      reader.onload = () => resolve(reader.result);
      reader.onerror = () => reject2(reader.error);
      reader.readAsArrayBuffer(file);
    });
  }

  if (browseButton) {
    browseButton.addEventListener("click", () => fileInput.click());
  }
  if (fileInput) {
    fileInput.addEventListener("change", (e) => handleFile(e.target.files[0]));
  }
  if (dropzone) {
    dropzone.addEventListener("click", () => fileInput && fileInput.click());
    ["dragenter", "dragover"].forEach((evt) =>
      dropzone.addEventListener(evt, (e) => {
        e.preventDefault();
        dropzone.classList.add("dragover");
      }),
    );
    ["dragleave", "drop"].forEach((evt) =>
      dropzone.addEventListener(evt, (e) => {
        e.preventDefault();
        dropzone.classList.remove("dragover");
      }),
    );
    dropzone.addEventListener("drop", (e) => {
      const file = e.dataTransfer.files && e.dataTransfer.files[0];
      handleFile(file);
    });
  }

  return { handleFile };
}
