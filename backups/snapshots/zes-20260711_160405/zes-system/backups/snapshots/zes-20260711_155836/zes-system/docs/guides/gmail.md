# Gmail Integration

Two methods are available for Gmail access: **Composio SDK** (OAuth) and **Gmail Tool** (IMAP/SMTP).

## Method 1: Composio SDK (Recommended)

Uses OAuth 2.0 with full Gmail API access via the @composio/client SDK.

### Status
- **Connection:** Active (`ca_oMyBtPXhgDu2`)
- **Email:** arfaxtrade@gmail.com
- **API Key:** `ak_aeZUsOJY8PCeLchjGEMy`

### Usage

```bash
# List emails
composio-gmail list 5

# Search emails
composio-gmail search "subject:alert"

# Send email
composio-gmail send '{"to":"user@example.com","subject":"Hello","body":"Test"}'
```

### Direct SDK Access

```bash
cd ~/composio-test
source ~/.config/composio/env.sh
node -e "
const { Composio } = await import('@composio/client');
const c = new Composio({ apiKey: process.env.COMPOSIO_API_KEY });
const r = await c.tools.execute('GMAIL_FETCH_EMAILS', {
  arguments: { max_results: 5 },
  connected_account_id: 'ca_oMyBtPXhgDu2',
  entity_id: 'arfaxtrade@gmail.com'
});
r.data.messages.forEach(m => {
  const h = m.payload.headers;
  console.log(h.find(x=>x.name==='From').value, h.find(x=>x.name==='Subject').value);
});
"
```

### SDK Resources

The SDK is installed at `~/composio-test/` and provides these APIs:
- `client.tools.execute()` — Execute a tool (GMAIL_FETCH_EMAILS, GMAIL_SEND_EMAIL, etc.)
- `client.connectedAccounts.list()` — List connected accounts
- `client.authConfigs.create()` — Create auth config for new connections
- `client.link.create()` — Generate OAuth link for user authorization

## Method 2: Gmail Tool (IMAP/SMTP)

Fallback method using Python stdlib IMAP and SMTP.

### Status
- **Connection:** Active
- **Messages:** ~3,600 inbox, ~3,200 unread
- **Config:** `~/.config/gmail-tool/config.json`

### Usage

```bash
gmail-tool status                    # Check connection
gmail-tool search "keyword"          # Search emails
gmail-tool send --to user@example.com --subject "Hi" --body "Hello"
```

## Setup New Connections

To connect a new Gmail account via Composio:

```bash
cd ~/composio-test
source ~/.config/composio/env.sh
node -e "
const { Composio } = await import('@composio/client');
const c = new Composio({ apiKey: process.env.COMPOSIO_API_KEY });
const config = await c.authConfigs.create({
  toolkit: { slug: 'gmail' },
  authScheme: 'OAUTH2'
});
const link = await c.link.create({
  auth_config_id: config.auth_config.id,
  user_id: 'user@gmail.com',
  alias: 'My Gmail'
});
console.log('Open:', link.redirect_url);
"
```
