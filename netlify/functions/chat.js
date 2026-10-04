// netlify/functions/chat.js
//
// Serverless proxy that keeps your API key server-side and hides the
// provider's CORS behaviour from the browser. The client sends
// { provider, model, key, system, name, messages } and gets back
// { reply: string }.
//
// This runs on Netlify's infrastructure. It never stores anything.

exports.handler = async (event) => {
  if (event.httpMethod !== 'POST') {
    return { statusCode: 405, body: 'Method Not Allowed' };
  }

  let body;
  try {
    body = JSON.parse(event.body || '{}');
  } catch (e) {
    return { statusCode: 400, body: JSON.stringify({ error: 'bad json' }) };
  }

  const { provider, model, key, system, messages } = body;
  if (!provider || !key || !Array.isArray(messages)) {
    return { statusCode: 400, body: JSON.stringify({ error: 'missing fields' }) };
  }

  try {
    let reply = '';

    if (provider === 'openai') {
      const r = await fetch('https://api.openai.com/v1/chat/completions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer ' + key
        },
        body: JSON.stringify({
          model: model || 'gpt-5-nano',
          messages: [{ role: 'system', content: system || '' }, ...messages]
        })
      });
      const j = await r.json();
      if (!r.ok) {
        return { statusCode: r.status, body: JSON.stringify({ error: j.error || j }) };
      }
      reply = j.choices?.[0]?.message?.content || '';
    } else if (provider === 'claude') {
      const r = await fetch('https://api.anthropic.com/v1/messages', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'x-api-key': key,
          'anthropic-version': '2023-06-01'
        },
        body: JSON.stringify({
          model: model || 'claude-haiku-4-5-20251001',
          max_tokens: 512,
          system: system || '',
          messages
        })
      });
      const j = await r.json();
      if (!r.ok) {
        return { statusCode: r.status, body: JSON.stringify({ error: j.error || j }) };
      }
      reply = j.content?.[0]?.text || '';
    } else if (provider === 'gemini') {
      const url = 'https://generativelanguage.googleapis.com/v1beta/models/' +
                  (model || 'gemini-3.5-flash-lite') +
                  ':generateContent?key=' + encodeURIComponent(key);
      const r = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          systemInstruction: { parts: [{ text: system || '' }] },
          contents: messages.map((m) => ({
            role: m.role === 'user' ? 'user' : 'model',
            parts: [{ text: m.content }]
          }))
        })
      });
      const j = await r.json();
      if (!r.ok) {
        return { statusCode: r.status, body: JSON.stringify({ error: j.error || j }) };
      }
      reply = j.candidates?.[0]?.content?.parts?.[0]?.text || '';
    } else {
      return { statusCode: 400, body: JSON.stringify({ error: 'unknown provider' }) };
    }

    return {
      statusCode: 200,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ reply })
    };
  } catch (err) {
    return {
      statusCode: 500,
      body: JSON.stringify({ error: String(err) })
    };
  }
};
