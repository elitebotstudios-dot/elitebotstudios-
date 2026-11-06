# Contact endpoint — owner setup guide

The contact form posts to `/api/contact`, a serverless function. It validates
every submission, discards honeypot hits, and **only sends mail if the deployment
has been configured to**. On an unconfigured deployment it returns
`503 {"ok":false,"error":"not_configured"}`, and the page opens a local email
draft while telling the visitor that nothing was transmitted.

That is the current live behaviour. No email has been delivered by this site, and
none is claimed to have been.

## What is missing

Two environment variables, both server-side only:

| Variable | Purpose | Example |
|---|---|---|
| `RESEND_API_KEY` | API key for Resend (https://resend.com) | `re_...` — never commit this |
| `CONTACT_TO` | destination inbox for enquiries | `contact@elitebotstudios.me` |

Neither is present in the Vercel project. Nothing else is required in code.

## Setup, step by step

1. **Create a Resend account** and add the sending domain
   (`elitebotstudios.me`). Resend will give you DNS records — SPF and DKIM, and
   optionally DMARC — which must be added at the DNS provider for the domain.
2. **Wait for verification.** Resend reports the domain as verified only after
   the records propagate. Sending from an unverified domain fails at the
   provider, not in this code.
3. **Create an API key** with send permission. Copy it once; it is not shown
   again.
4. **Add both variables in Vercel**: Project → Settings → Environment Variables.
   Add them for Production (and Preview, if you want previews to send). A
   redeploy is required; environment changes do not apply to a running
   deployment.
5. **Verify from outside**: `curl -X POST https://elitebotstudios.me/api/contact`
   with a valid JSON body should now return `{"ok":true,"delivered":true}`
   instead of `503 not_configured`.

## What the endpoint already does

- Rejects `GET` with `405`.
- Validates name, email, category and message length, returning `422` with
  per-field messages.
- Accepts only six defined enquiry categories; anything else is rejected.
- Silently discards honeypot submissions (`200 {"ok":true,"delivered":false}`) so
  a bot cannot tell it was caught.
- Strips control characters and caps every field length.
- Keeps the API key server-side; it is never sent to the browser.
- Sends a plain-text body with the reply-to set to the visitor's address.

## Privacy

The endpoint does not log submissions. The site's privacy page describes the
form, the third-party processor and the fallback. If you change the provider,
update that page in the same commit — the privacy statement names what happens to
the data, and it must stay true.

## Testing that is deliberately not done

A real end-to-end delivery test requires sending a message to the destination
inbox. That has not been performed, because no credentials exist and sending
mail from an unverified domain would fail anyway. Once the variables are set, one
test message — clearly labelled as a test — is the correct verification step.
