# Porchlight

A patient personal assistant for people who don't like technology. It interviews you one question at a time, then builds your Home page around your answers.

**Live version (inside Claude):** https://claude.ai/artifact/ER7K6enksyXCfnRBbQ5ojo

## What it does

- **Setup interview**: asks your name, a name for your helper, and what you want help with. Then it walks you through each part in plain words, with no videos.
- **Mail**: reads your newest Gmail and sorts it into *Needs your answer*, *Good to know*, *Be careful (may be a scam)*, and *Can wait*. You can have an email read aloud, explained simply, or answered. Nothing is sent until you tap **Send** and then **Yes**.
- **Calendar**: today's and tomorrow's Google Calendar events on the Home page.
- **To-do list**: big check boxes. Add items yourself, from an email, or by asking the helper.
- **Talk**: chat with the helper about jokes, Bible verses, scam checks, or writing a note. It can add items to your to-do list.
- **Family notes**: a shared message board for family members you invite through Claude's Share menu.
- **Weather, stocks, bank, favorite websites**: big buttons that open the real sites. The bank tile includes scam-safety reminders.
- **Built for older eyes**: three text sizes, high contrast, light and dark themes, "Read this to me" on every question, and a Help button on every screen.

## Files

| File | Purpose |
| --- | --- |
| `app.html` | The page as published to Claude (no `<html>` wrapper; Claude adds it). |
| `index.html` | The same page with a standard wrapper so it opens in any browser. |

## Running it

- **Inside Claude (full version):** open the live link above. Claude asks once for permission to use Gmail, Google Calendar, and Claude itself.
- **In any browser (limited version):** open `index.html`. The interview, to-do list, jokes, verses, and links all work and are saved on that device only. The page shows example emails, and the chat answers only simple requests.

After editing `app.html`, rebuild `index.html` by wrapping it with a doctype, `<head>`, and `<body>`. See the commit that added this folder.

## Known limits

- Only Gmail is read directly. For Outlook, Yahoo, AOL, or iCloud, the setup shows steps for forwarding mail to Gmail.
- Phone text messages can't be read yet. Phones don't allow it, so the helper offers to check pasted texts for scams instead.
- Live weather and stock prices open on weather.gov and Yahoo Finance. Claude pages can't fetch outside data on their own.
- Porchlight never connects to bank accounts and never asks for passwords. That is on purpose.
