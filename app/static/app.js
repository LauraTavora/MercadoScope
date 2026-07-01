let chartInstance = null;
const tenantSlug = document.body.dataset.tenant || 'demo-store';

const money = (value) => new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value || 0);
const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

async function api(url, options = {}) {
  const response = await fetch(url, {
    headers: { 'Content-Type': 'application/json', 'X-Tenant-ID': tenantSlug, ...(options.headers || {}) },
    ...options,
  });
  if (!response.ok) {
    let message = `Erro HTTP ${response.status}`;
    try { const data = await response.json(); message = data.detail || message; } catch (_) {}
    throw new Error(message);
  }
  return response.json();
}

function showFeedback(message, isError = false) {
  const box = document.getElementById('job-feedback');
  box.textContent = message;
  box.classList.remove('hidden');
  box.classList.toggle('error', isError);
}

function setLive(job) {
  document.getElementById('live-results').classList.remove('hidden');
  document.getElementById('live-title').textContent = job.query;
  const status = document.getElementById('live-status');
  status.textContent = job.status;
  status.className = `status ${job.status}`;
  document.getElementById('progress-bar').style.width = `${job.progress}%`;
}

async function pollJob(jobId) {
  for (;;) {
    const job = await api(`/api/v1/jobs/${jobId}`);
    setLive(job);
    if (job.status === 'completed') {
      showFeedback(`Coleta concluída com ${job.item_count} produtos.`);
      await renderProducts(jobId);
      return;
    }
    if (job.status === 'failed') {
      showFeedback(job.error_message || 'A coleta falhou.', true);
      return;
    }
    await sleep(900);
  }
}

async function renderProducts(jobId) {
  const products = await api(`/api/v1/jobs/${jobId}/products`);
  document.getElementById('result-actions').classList.remove('hidden');
  document.getElementById('analytics').classList.remove('hidden');
  document.getElementById('csv-link').href = `/api/v1/jobs/${jobId}/export.csv`;
  document.getElementById('pdf-link').href = `/api/v1/jobs/${jobId}/report.pdf`;

  const body = document.getElementById('products-body');
  body.innerHTML = products.slice(0, 50).map((product) => `
    <tr>
      <td>${product.position}</td>
      <td><a target="_blank" rel="noopener noreferrer" href="${product.product_url}">${escapeHtml(product.title)}</a></td>
      <td>${money(product.price)}</td>
      <td>${product.rating ?? '—'}</td>
      <td>${product.sold_quantity ?? '—'}</td>
    </tr>`).join('');

  const buckets = {};
  for (const product of products) {
    const start = Math.floor(product.price / 500) * 500;
    const key = `${money(start)}–${money(start + 499.99)}`;
    buckets[key] = (buckets[key] || 0) + 1;
  }
  if (chartInstance) chartInstance.destroy();
  chartInstance = new Chart(document.getElementById('price-chart'), {
    type: 'bar',
    data: { labels: Object.keys(buckets), datasets: [{ label: 'Produtos', data: Object.values(buckets) }] },
    options: { responsive: true, maintainAspectRatio: false, plugins: { title: { display: true, text: 'Distribuição de preços' }, legend: { display: false } } },
  });
}

function escapeHtml(value) {
  return String(value).replace(/[&<>'"]/g, (char) => ({ '&':'&amp;', '<':'&lt;', '>':'&gt;', "'":'&#39;', '"':'&quot;' }[char]));
}

document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('job-form');
  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    const payload = {
      query: document.getElementById('query').value,
      category_url: document.getElementById('category_url').value || null,
      max_pages: Number(document.getElementById('max_pages').value),
      sort: document.getElementById('sort').value,
    };
    showFeedback('Job criado. Iniciando coleta...');
    try {
      const job = await api('/api/v1/jobs', { method: 'POST', body: JSON.stringify(payload) });
      setLive(job);
      document.getElementById('live-results').scrollIntoView({ behavior: 'smooth' });
      await pollJob(job.id);
    } catch (error) {
      showFeedback(error.message, true);
    }
  });

  const tour = document.getElementById('tour');
  if (!localStorage.getItem('mercadoscope-tour-seen')) tour.classList.remove('hidden');
  document.getElementById('close-tour').addEventListener('click', () => {
    localStorage.setItem('mercadoscope-tour-seen', '1');
    tour.classList.add('hidden');
  });
});
