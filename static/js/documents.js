function initDocumentsPage() {
    loadDocumentsTable();
    setupDropzone();
}

function loadDocumentsTable() {
    fetch('/api/documents')
        .then(res => res.json())
        .then(documents => {
            const tbody = document.getElementById('documentsTableBody');
            tbody.innerHTML = '';

            if (documents.length === 0) {
                tbody.innerHTML = `
                    <tr>
                        <td colspan="7" class="text-center py-5">
                            <i class="bi bi-folder-x text-muted fs-1 mb-2 d-block"></i>
                            <h5 class="fw-bold">No Documents Uploaded</h5>
                            <p class="text-muted small">Upload your first PDF document above to start indexing into the FAISS vector database.</p>
                        </td>
                    </tr>
                `;
                return;
            }

            documents.forEach(doc => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td class="ps-4 fw-bold">
                        <i class="bi bi-file-earmark-pdf-fill text-danger me-2 fs-5 align-middle"></i>
                        ${doc.filename}
                    </td>
                    <td><span class="badge bg-light text-dark border">${doc.pages} Pages</span></td>
                    <td><span class="badge bg-light text-primary border">${doc.chunk_count} Chunks</span></td>
                    <td><small class="text-muted font-monospace">${doc.file_size_formatted}</small></td>
                    <td><span class="badge bg-success"><i class="bi bi-check-circle me-1"></i>${doc.status}</span></td>
                    <td><small class="text-muted">${doc.uploaded_at || ''}</small></td>
                    <td class="pe-4 text-end">
                        <div class="btn-group">
                            <button class="btn btn-sm btn-outline-secondary" onclick="reprocessDoc(${doc.id})" title="Reprocess & Re-index"><i class="bi bi-arrow-repeat"></i></button>
                            <button class="btn btn-sm btn-outline-danger" onclick="deleteDoc(${doc.id}, '${doc.filename}')" title="Delete Document"><i class="bi bi-trash3"></i></button>
                        </div>
                    </td>
                `;
                tbody.appendChild(tr);
            });
        });
}

function setupDropzone() {
    const dropzone = document.getElementById('docsDropzone');
    const fileInput = document.getElementById('docsFileInput');

    dropzone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropzone.classList.add('dragover');
    });

    dropzone.addEventListener('dragleave', () => {
        dropzone.classList.remove('dragover');
    });

    dropzone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropzone.classList.remove('dragover');
        if (e.dataTransfer.files.length > 0) {
            uploadFiles(e.dataTransfer.files);
        }
    });

    fileInput.addEventListener('change', () => {
        if (fileInput.files.length > 0) {
            uploadFiles(fileInput.files);
        }
    });
}

function uploadFiles(files) {
    const statusAlert = document.getElementById('uploadStatusAlert');
    const statusText = document.getElementById('uploadStatusText');
    const formData = new FormData();

    for (let i = 0; i < files.length; i++) {
        formData.append('files', files[i]);
    }

    statusAlert.classList.remove('d-none');
    statusText.textContent = `Processing ${files.length} PDF file(s)... Extracting text, chunking & generating FAISS embeddings...`;

    fetch('/api/upload', {
        method: 'POST',
        body: formData
    })
    .then(res => res.json())
    .then(data => {
        statusAlert.classList.add('d-none');
        if (data.error) {
            alert("Upload Error: " + data.error);
        } else {
            loadDocumentsTable();
        }
    })
    .catch(err => {
        statusAlert.classList.add('d-none');
        alert("Upload failed: " + err);
    });
}

function deleteDoc(docId, filename) {
    if (!confirm(`Are you sure you want to delete '${filename}'? This will remove its vectors and rebuild the index.`)) return;

    fetch(`/api/documents/${docId}`, { method: 'DELETE' })
        .then(res => res.json())
        .then(data => {
            loadDocumentsTable();
        })
        .catch(err => {
            alert("Delete failed: " + err);
        });
}

function reprocessDoc(docId) {
    fetch(`/api/documents/${docId}/reprocess`, { method: 'POST' })
        .then(res => res.json())
        .then(data => {
            loadDocumentsTable();
        });
}
