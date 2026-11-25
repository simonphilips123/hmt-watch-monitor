# HMT Watch Stock Monitor (GitHub Actions)

Automated stock monitor for **HMT Men's Gandaberunda JGSS 01**:
`https://www.hmtwatches.in/product-1180-hmt-mens-gandaberunda-jgss-01`

Runs every **30 minutes** for free on **GitHub Actions** and sends an instant alert via **Telegram** (recommended, 1-minute setup, no slot limits) and/or **Meta WhatsApp Cloud API** as soon as the watch is available to buy.

---

## 1. Choose Your Free Notification Channel

### Option A: Telegram Bot (Recommended — 1 minute, 100% free & unlimited)
1. Open Telegram and message **`@BotFather`**.
2. Send `/newbot`, choose a name and username, and copy the **Bot Token** it gives you.
3. Start a chat with your new bot (click the link `@BotFather` gives you and press **Start**).
4. Message **`@userinfobot`** on Telegram to get your numeric **Chat ID** (e.g., `123456789`).

### Option B: Meta WhatsApp Cloud API (Official WhatsApp Free Tier)
1. Go to [developers.facebook.com](https://developers.facebook.com) → **My Apps → Create App → Other → Business**.
2. Add the **WhatsApp** product → **API Setup**.
3. Copy your **Temporary/System Access Token**, **Phone Number ID**, and add your own WhatsApp number under **To** (test recipient).

*(You can configure Option A, Option B, or both!)*

---

## 2. Push This Project to GitHub

```bash
git push -u origin main
```

---

## 3. Add GitHub Repository Secrets

In your GitHub repository, go to **Settings → Secrets and variables → Actions → New repository secret**:

### For Telegram (Option A):
| Secret Name | Example Value | Description |
| :--- | :--- | :--- |
| `TELEGRAM_BOT_TOKEN` | `7123456789:AAH...` | Token from `@BotFather` |
| `TELEGRAM_CHAT_ID` | `123456789` | Your numeric Chat ID from `@userinfobot` |

### For Meta WhatsApp Cloud API (Option B):
| Secret Name | Example Value | Description |
| :--- | :--- | :--- |
| `WHATSAPP_TOKEN` | `EAAG...` | Meta WhatsApp Cloud API token |
| `WHATSAPP_PHONE_NUMBER_ID` | `10987654321` | Phone Number ID from Meta App Dashboard |
| `WHATSAPP_TO` | `+919876543210` | Your WhatsApp number with country code |

### Optional AI Fallback:
| Secret Name | Example Value | Description |
| :--- | :--- | :--- |
| `GEMINI_API_KEY` | `AIza...` | Free Google AI Studio key used only if page HTML changes |

---

## 4. Test Immediately

1. Open the **Actions** tab in your GitHub repository.
2. Select **HMT Watch Stock Monitor**.
3. Click **Run workflow** → check **`test_notify`** (`true`) → click **Run workflow**.
4. You should receive a test alert within a few seconds.

---

## 5. Notes

- **30-minute schedule:** GitHub Actions `cron: "*/30 * * * *"` runs in the cloud without your PC, though GitHub may queue scheduled runs by a few minutes during peak hours.
- **60-day inactivity rule:** GitHub automatically pauses scheduled workflows if a repository has no commits/activity for 60 days. Pushing a tiny commit (or clicking **Enable workflow**) every couple of months keeps it active.
