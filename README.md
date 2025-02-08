# 🚀 Nitro Code Generator & Checker 🎮

## 🔥 Overview

This script is designed to **generate, check**, and **redeem Discord Nitro codes** with advanced rate-limiting handling, automatic redemption, and live status tracking. 💥 Whether you're looking to redeem a Nitro code or test out multiple codes, this tool makes the process seamless and efficient! 

Created by: **Ambry** (Modified by ChatGPT)  
License: **MIT** 📄

## 🛠 Features

- **Code Generation**: Generates random 16-character Discord Nitro gift codes 🎯.
- **Rate-Limit Handling**: Automatically handles per-endpoint rate limits and retries ♻️.
- **Auto Redemption**: Automatically redeems valid Nitro codes using your Discord token 🔑.
- **Webhook Notifications**: Sends notifications to a Discord webhook when a valid code is found 📬.
- **Live Console Status**: Displays real-time status of valid/invalid codes being checked in the console 🖥️.

## 📦 Requirements

To run this script, you'll need the following Python modules:

- [requests](https://pypi.org/project/requests/) 📦
- [discord_webhook](https://pypi.org/project/discord-webhook/) (optional for webhook notifications) 📢

Install them via pip:

```bash
pip install requests discord-webhook discord.py-self
```

## ⚙️ Setup

1. Clone or download the script.
2. Install required dependencies (e.g., `requests` and `discord-webhook`).
3. **Discord Token**: You'll need your **Discord token** to redeem Nitro codes.
4. Optionally, set up a **Discord webhook** to receive notifications when a valid code is found.

## 🏃‍♂️ How to Run

Run the script using Python:

```bash
python main.py
```

### The bot will prompt you for:
1. **Discord Token**: Your token is required for redeeming Nitro codes.
2. **Webhook URL** (Optional): If enabled, enter a valid Discord webhook URL for notifications.

### What Happens Next:
- The script will **continuously generate Nitro codes** and test them against Discord's endpoints 🔄.
- If a **valid code** is found, it will be redeemed automatically if you provided a valid token 🔑.
- A **live status message** will display the number of valid and invalid codes checked 🔢.

## 🚨 Important Notes

- **Disclaimer**: The use of this script for generating and redeeming Nitro codes may violate Discord's Terms of Service. Misuse can lead to account suspension or bans. **Use this tool responsibly and at your own risk.** ⚠️
- **Webhook Notifications**: To enable webhook notifications, install the `discord-webhook` module and provide a valid URL. 🛠️
- Ensure that your **Discord token** is kept secure and not shared with anyone! 🔒

## 📈 Summary

- **Generate and test** multiple Nitro codes quickly and efficiently.
- **Handle rate-limits** automatically and retry endpoints as needed.
- **Redeem valid codes** using your Discord token.
- **Get notified** via webhook whenever a valid code is found.

--

🎉 **Happy Nitro Generating!** 🚀
