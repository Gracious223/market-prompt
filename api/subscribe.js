// Market Prompt — newsletter signup endpoint (Vercel serverless function).
//
// Collects an email from the site's signup form and adds it to a Resend
// Audience (the contact list). No database needed; emails never touch the repo.
//
// Required Vercel environment variables:
//   RESEND_API_KEY      — your Resend API key
//   RESEND_AUDIENCE_ID  — the Resend audience (list) to add contacts to
//
// While those are unset, the endpoint returns a clear "not configured" message
// and the site's form falls back to opening the visitor's mail client.

const EMAIL_RE = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;

module.exports = async function handler(req, res) {
  // Allow the form to post from the Vercel site or the GitHub Pages mirror.
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader("Access-Control-Allow-Methods", "POST, OPTIONS");
  res.setHeader("Access-Control-Allow-Headers", "Content-Type");
  if (req.method === "OPTIONS") return res.status(204).end();
  if (req.method !== "POST") return res.status(405).json({ error: "Method not allowed" });

  let email = "";
  try {
    const body = typeof req.body === "string" ? JSON.parse(req.body || "{}") : req.body || {};
    email = String(body.email || "").trim().toLowerCase();
  } catch (_) {
    /* fall through to validation */
  }
  if (!EMAIL_RE.test(email)) {
    return res.status(400).json({ error: "Please enter a valid email." });
  }

  const key = process.env.RESEND_API_KEY;
  const audienceId = process.env.RESEND_AUDIENCE_ID;
  if (!key || !audienceId) {
    return res.status(503).json({ error: "Sign-up isn't switched on yet — check back soon." });
  }

  try {
    const r = await fetch(`https://api.resend.com/audiences/${audienceId}/contacts`, {
      method: "POST",
      headers: { Authorization: `Bearer ${key}`, "Content-Type": "application/json" },
      body: JSON.stringify({ email, unsubscribed: false }),
    });
    // 409 = already a contact; treat as success so repeat signups feel fine.
    if (!r.ok && r.status !== 409) {
      return res.status(502).json({ error: "Couldn't subscribe right now — please try again." });
    }
    return res.status(200).json({ ok: true });
  } catch (_) {
    return res.status(502).json({ error: "Couldn't subscribe right now — please try again." });
  }
};
