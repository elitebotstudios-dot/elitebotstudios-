/**
 * Contact delivery endpoint (Vercel serverless function).
 *
 * Delivery requires two environment variables set in the Vercel project:
 *   RESEND_API_KEY  – API key for Resend (https://resend.com)
 *   CONTACT_TO      – destination inbox, e.g. contact@elitebotstudios.me
 * Optional:
 *   CONTACT_FROM    – verified sender, defaults to Resend's test sender
 *
 * Without those variables the endpoint answers 503 "not_configured" and the
 * website falls back to opening a local email draft. It never pretends a
 * message was delivered.
 *
 * No message bodies are logged; only status codes.
 */

const MAX = { name: 100, email: 254, organization: 120, category: 80, message: 1200 };
const CATEGORIES = [
  'Engineering collaboration',
  'Academic or research discussion',
  'Research opportunity',
  'Internship or job opportunity',
  'Hardware project inquiry',
  'General question'
];

function clean(value, limit) {
  return String(value == null ? '' : value).replace(/[\u0000-\u001f\u007f]/g, ' ').trim().slice(0, limit);
}

function validEmail(value) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(value) && value.length <= MAX.email;
}

module.exports = async function handler(req, res) {
  res.setHeader('Cache-Control', 'no-store');

  if (req.method !== 'POST') {
    res.status(405).json({ ok: false, error: 'method_not_allowed' });
    return;
  }

  let body = req.body;
  if (typeof body === 'string') {
    try { body = JSON.parse(body); } catch (_) { body = null; }
  }
  if (!body || typeof body !== 'object') {
    res.status(400).json({ ok: false, error: 'invalid_body' });
    return;
  }

  /* Honeypot: real visitors never fill this hidden field. */
  if (clean(body.website, 200)) {
    res.status(200).json({ ok: true, delivered: false });
    return;
  }

  const name = clean(body.name, MAX.name);
  const email = clean(body.email, MAX.email);
  const organization = clean(body.organization, MAX.organization);
  const category = clean(body.category, MAX.category);
  const message = clean(body.message, MAX.message);

  const errors = {};
  if (name.length < 2) errors.name = 'Enter your name.';
  if (!validEmail(email)) errors.email = 'Enter a valid email address.';
  if (message.length < 20) errors.message = 'Please add at least 20 characters.';
  if (CATEGORIES.indexOf(category) === -1) errors.category = 'Choose an inquiry type.';

  if (Object.keys(errors).length) {
    res.status(422).json({ ok: false, error: 'validation', fields: errors });
    return;
  }

  const apiKey = process.env.RESEND_API_KEY;
  const to = process.env.CONTACT_TO;
  const from = process.env.CONTACT_FROM || 'Elite Bot Studios <onboarding@resend.dev>';

  if (!apiKey || !to) {
    res.status(503).json({ ok: false, error: 'not_configured' });
    return;
  }

  const text = [
    'Name: ' + name,
    'Email: ' + email,
    'Organization: ' + (organization || 'Not provided'),
    'Inquiry: ' + category,
    '',
    message
  ].join('\n');

  try {
    const response = await fetch('https://api.resend.com/emails', {
      method: 'POST',
      headers: {
        Authorization: 'Bearer ' + apiKey,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        from,
        to: [to],
        reply_to: email,
        subject: 'Elite Bot Studios — ' + category,
        text
      })
    });

    if (!response.ok) {
      /* Status only; the provider's message may echo the payload. */
      res.status(502).json({ ok: false, error: 'provider_rejected', status: response.status });
      return;
    }
    res.status(200).json({ ok: true, delivered: true });
  } catch (_) {
    res.status(502).json({ ok: false, error: 'provider_unreachable' });
  }
};
