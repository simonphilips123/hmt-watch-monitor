# HMT Watch Stock Monitor (GitHub Actions + WhatsApp)

Automated stock monitor for **HMT Men's Gandaberunda JGSS 01**:
`https://www.hmtwatches.in/product-1180-hmt-mens-gandaberunda-jgss-01`

Runs every **30 minutes** for free on **GitHub Actions** and sends an instant **WhatsApp** alert via **CallMeBot** as soon as the watch is available to buy.

---

## 1. One-Time CallMeBot WhatsApp Setup (1 minute, Free)

1. Save the CallMeBot phone number in your phone contacts: **`+34 644 71 98 38`** (or check [callmebot.com](https://www.callmebot.com/blog/free-api-whatsapp-messages/) for the latest activation number).
2. Send this exact WhatsApp message to that contact:
   ```text
   I allow callmebot to send me messages
   ```
3. CallMeBot will reply with your **`apikey`**. Keep it handy for Step 3.

---

## 2. Push This Project to GitHub

1. Create a new repository on GitHub (public or private; public repos get unlimited free GitHub Actions minutes).
2. Push this folder to your GitHub repository:
   ```bash
   git init
   git add .
   git commit -m "Initial HMT watch monitor"
   git branch -M main
   git remote add origin https://github.com/<YOUR_USERNAME>/<YOUR_REPO>.git
   git push -u origin main
   ```

---

## 3. Add GitHub Repository Secrets

In your GitHub repository, go to **Settings → Secrets and variables → Actions → New repository secret** and add:

| Secret Name | Required | Example Value | Description |
| :--- | :--- | :--- | :--- |
| `CALLMEBOT_PHONE` | Yes | `+919876543210` | Your WhatsApp number with country code |
| `CALLMEBOT_APIKEY` | Yes | `1234567` | API key received from CallMeBot |
| `GEMINI_API_KEY` | Optional | `AIza...` | Free Google AI Studio key used only as fallback if page HTML changes |

---

## 4. Test Immediately

1. Open the **Actions** tab in your GitHub repository.
2. Select **HMT Watch Stock Monitor**.
3. Click **Run workflow** → check **`test_notify`** (`true`) → click **Run workflow**.
4. You should receive a test WhatsApp message within a few seconds.

---

## 5. Notes & Limitations

- **30-minute schedule:** GitHub Actions `cron: "*/30 * * * *"` runs in the cloud without your PC, though GitHub may queue scheduled runs by a few minutes during peak hours.
- **60-day inactivity rule:** GitHub automatically pauses scheduled workflows if a repository has no commits/activity for 60 days. Pushing a tiny commit (or manually clicking **Enable workflow**) every couple of months keeps it active.
- **Auto-add-to-cart:** Because GitHub Actions runs in a fresh, stateless VM each time, it sends an instant WhatsApp alert with the direct buy link rather than storing your HMT account password/cookies in CI.
