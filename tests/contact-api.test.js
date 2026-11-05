/* Server-side contact endpoint: method guard, validation, honeypot, and the
   honest "not configured" response. No network calls are made.
   Usage: node tests/contact-api.test.js                                  */
const assert = require('assert');
const handler = require('../api/contact.js');

function mockRes() {
  const res = {
    statusCode: 0,
    body: null,
    headers: {},
    setHeader(k, v) { this.headers[k.toLowerCase()] = v; },
    status(code) { this.statusCode = code; return this; },
    json(payload) { this.body = payload; return this; }
  };
  return res;
}

async function call(req) {
  const res = mockRes();
  await handler(req, res);
  return res;
}

(async () => {
  let r = await call({ method: 'GET', body: null });
  assert.strictEqual(r.statusCode, 405, 'GET must be rejected');

  r = await call({ method: 'POST', body: 'not json' });
  assert.strictEqual(r.statusCode, 400, 'malformed body must be rejected');

  r = await call({ method: 'POST', body: { name: 'A', email: 'nope', category: 'Engineering collaboration', message: 'short' } });
  assert.strictEqual(r.statusCode, 422, 'invalid submission must be 422');
  assert.ok(r.body.fields.name && r.body.fields.email && r.body.fields.message, 'field errors returned');

  r = await call({ method: 'POST', body: { name: 'Bot', email: 'bot@example.com', category: 'Engineering collaboration', message: 'This is a sufficiently long automated message.', website: 'spam.example' } });
  assert.strictEqual(r.statusCode, 200);
  assert.strictEqual(r.body.delivered, false, 'honeypot submissions are not delivered');

  delete process.env.RESEND_API_KEY;
  delete process.env.CONTACT_TO;
  r = await call({ method: 'POST', body: { name: 'QA Visitor', email: 'qa@example.com', organization: 'NUST', category: 'Academic or research discussion', message: 'A valid message long enough to pass validation.' } });
  assert.strictEqual(r.statusCode, 503, 'unconfigured delivery must report 503');
  assert.strictEqual(r.body.error, 'not_configured');
  assert.ok(!JSON.stringify(r.body).includes('A valid message'), 'no message echoed in the response');

  process.env.RESEND_API_KEY = 'test-key';
  process.env.CONTACT_TO = 'contact@elitebotstudios.me';
  const realFetch = global.fetch;
  let sent = null;
  global.fetch = async (url, init) => {
    sent = { url, init };
    return { ok: true, status: 200 };
  };
  r = await call({ method: 'POST', body: { name: 'QA Visitor', email: 'qa@example.com', category: 'General question', message: 'A valid message long enough to pass validation.' } });
  assert.strictEqual(r.statusCode, 200);
  assert.strictEqual(r.body.delivered, true);
  assert.ok(sent && sent.url.includes('api.resend.com'), 'provider called when configured');
  assert.ok(!sent.init.headers.Authorization.includes('test-key') === false, 'key sent to provider only');
  assert.ok(sent.init.body.includes('reply_to'), 'reply-to set to visitor address');

  global.fetch = async () => ({ ok: false, status: 422 });
  r = await call({ method: 'POST', body: { name: 'QA Visitor', email: 'qa@example.com', category: 'General question', message: 'A valid message long enough to pass validation.' } });
  assert.strictEqual(r.statusCode, 502, 'provider rejection surfaces as 502');

  global.fetch = realFetch;
  delete process.env.RESEND_API_KEY;
  delete process.env.CONTACT_TO;
  console.log('PASS: contact endpoint validation, honeypot, unconfigured fallback, provider success and failure');
})().catch((e) => {
  console.error('FAIL:', e.message);
  process.exit(1);
});
