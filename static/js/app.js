// Global Utility Functions

function formatMarkdown(text) {
    if (!text) return "";
    let html = text
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;");

    // Headers
    html = html.replace(/### (.*?)(<br>|\n|$)/g, '<h5 class="fw-bold mt-3 mb-2 text-dark">$1</h5>');
    html = html.replace(/## (.*?)(<br>|\n|$)/g, '<h4 class="fw-bold mt-3 mb-2 text-dark">$1</h4>');
    html = html.replace(/# (.*?)(<br>|\n|$)/g, '<h3 class="fw-bold mt-3 mb-2 text-dark">$1</h3>');

    // Bold & Italic
    html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    html = html.replace(/\*(.*?)\*/g, '<em>$1</em>');

    // Code blocks
    html = html.replace(/```(.*?)```/gs, '<pre class="bg-dark text-white p-3 rounded-3 my-2 font-monospace"><code>$1</code></pre>');
    html = html.replace(/`(.*?)`/g, '<code class="bg-light px-1 py-0.5 rounded text-danger">$1</code>');

    // Lists
    html = html.replace(/^\s*-\s+(.*)$/gm, '<li class="ms-3 mb-1">$1</li>');
    html = html.replace(/^\s*\d+\.\s+(.*)$/gm, '<li class="ms-3 mb-1">$1</li>');

    // Paragraphs / Newlines
    html = html.replace(/\n/g, '<br>');
    return html;
}

function copyToClipboard(btn, text) {
    navigator.clipboard.writeText(text).then(() => {
        const originalHtml = btn.innerHTML;
        btn.innerHTML = '<i class="bi bi-check2 me-1 text-success"></i> Copied!';
        btn.classList.add('btn-light');
        setTimeout(() => {
            btn.innerHTML = originalHtml;
            btn.classList.remove('btn-light');
        }, 2000);
    }).catch(err => {
        console.error('Failed to copy: ', err);
    });
}
