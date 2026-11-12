// simple chat polling + send via fetch
function startChatPolling(convId, onNewMessages) {
  let last = null;
  async function poll() {
    let url = `/api/chat/${convId}/messages`;
    if (last) url += `?since=${encodeURIComponent(last)}`;
    try {
      const res = await fetch(url);
      const data = await res.json();
      if (data.messages && data.messages.length) {
        last = data.messages[data.messages.length - 1].created_at;
        onNewMessages(data.messages);
      }
    } catch (e) {
      console.error(e);
    }
    setTimeout(poll, 3000);
  }
  poll();
}

async function sendChatMessage(convId, body) {
  const res = await fetch(`/api/chat/${convId}/send`, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({body})
  });
  return res.json();
}
