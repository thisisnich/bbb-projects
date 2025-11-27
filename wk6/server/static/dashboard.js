const tableBody = document.getElementById('clientsTable');
const refreshBtn = document.getElementById('refreshBtn');
const serverTime = document.getElementById('serverTime');

async function fetchJSON(url, options) {
  const response = await fetch(url, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || response.statusText);
  }
  return response.json();
}

function formatDate(value) {
  if (!value) return '—';
  return new Date(value).toLocaleString();
}

function renderRows(clients) {
  if (!clients.length) {
    tableBody.innerHTML =
      '<tr><td colspan="8" class="text-center text-muted">No clients yet</td></tr>';
    return;
  }

  tableBody.innerHTML = clients
    .map((client) => {
      const payload = client.last_payload && Object.keys(client.last_payload).length
        ? JSON.stringify(client.last_payload)
        : '—';
      return `
        <tr>
          <td><code>${client.client_id}</code></td>
          <td>${client.board_type}</td>
          <td>${client.sensor_type}</td>
          <td>${client.location}</td>
          <td><span class="badge bg-${client.status === 'streaming'
            ? 'success'
            : client.status === 'connected'
              ? 'primary'
              : 'secondary'}">${client.status}</span></td>
          <td>${formatDate(client.last_seen)}</td>
          <td class="small">${payload}</td>
          <td class="d-flex gap-1">
            <button class="btn btn-sm btn-success" data-target="${client.client_id}" data-command="start">Start</button>
            <button class="btn btn-sm btn-warning" data-target="${client.client_id}" data-command="stop">Stop</button>
            <button class="btn btn-sm btn-secondary" data-target="${client.client_id}" data-command="reset">Reset</button>
          </td>
        </tr>
      `;
    })
    .join('');
}

async function refreshClients() {
  try {
    const data = await fetchJSON('/api/clients');
    renderRows(data.clients || []);
    serverTime.textContent = new Date().toLocaleTimeString();
  } catch (error) {
    console.error(error);
    alert(`Failed to load clients: ${error.message}`);
  }
}

async function sendCommand(command, target = 'all') {
  try {
    await fetchJSON('/api/command', {
      method: 'POST',
      body: JSON.stringify({ command, target }),
    });
    refreshClients();
  } catch (error) {
    console.error(error);
    alert(`Failed to send command: ${error.message}`);
  }
}

document.addEventListener('click', (event) => {
  const button = event.target.closest('button[data-command]');
  if (!button) return;
  const command = button.dataset.command;
  const target = button.dataset.target || 'all';
  sendCommand(command, target);
});

refreshBtn?.addEventListener('click', refreshClients);
setInterval(refreshClients, 4000);
refreshClients();

