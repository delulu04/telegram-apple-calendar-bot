# Telegram to Apple Calendar bot

Type an event in Telegram, tap how often it repeats, and it lands in your iCloud calendar (so it shows on your iPhone, Mac and iPad). Before saving, the bot checks your calendars and warns you about clashes. If you colour-code with several calendars, add a `#tag` to pick which one.

Forked from [seandias/telegram-apple-calendar-bot](https://github.com/seandias/telegram-apple-calendar-bot). This fork adds calendar tags, shorter durations (`2h`, `90min`), titles kept as typed, `/refresh`, and protection against the bot freezing when iCloud is slow.

```
You:  Football next tuesday 8-10pm
Bot:  📅 Football
      Tue 10 Nov, 8pm to 10pm
      Repeat?  [Doesn't repeat] [Weekly] [Every 2 weeks] [Daily] [Monthly] [Cancel]
You:  (tap Weekly)
Bot:  ⚠️ Clashes in the next 3 months:
      • Tue 17 Nov: Dinner (7:30pm–9pm)
      Add anyway?  [Add anyway] [Cancel]
```

## What it understands

| You type | Result |
|---|---|
| `Football next tuesday 8-10pm` | Tue 10 Nov, 8pm to 10pm |
| `Dentist 12 nov 3pm` | 1 hour by default |
| `Dinner fri 7:30pm for 2h` | Custom length |
| `gym mon 7pm 2h` / `90min` / `1.5h` / `1h30` | Same, "for" is optional |
| `gym mon 16 nov 7pm` | Weekday next to a date is fine, it won't end up in the title |
| `IS4234 lect wed 2-4pm #sch` | Goes straight to the SCHOOL calendar (see below) |
| `lunch tmr 11-1pm` | 11am to 1pm |
| `Party sat 10pm-1am` | Runs past midnight |
| `Standup 20/11 09:30-10:00` | Dates are day/month |
| `Review next week wed 3-4pm` | Wednesday of next week |
| `Sandra's birthday 14/12` | No time means all day |
| `In Korea 21/12-7/1` | Trip banner across those days, marked Free |
| `Taiwan 16-21 dec` | Same, other date styles work too |

Rules worth knowing:
- `next fri` means Friday of next week (said on Wed 4 Nov, that's Fri 13 Nov). `fri` alone means the coming Friday (Fri 6 Nov), which can be today.
- A time with no date goes today, or tomorrow if it has already passed.
- Without am/pm, hours 1 to 6 are read as afternoon/evening and 7 to 11 as morning. Add `pm` if in doubt; the bot always shows what it understood before saving.

- `45m` on its own isn't read as a length (so names like "Run 5m" survive). Write `45min` or `for 45m`.
- Titles are capitalised ("Gym") unless you set `CAPITALISE_TITLES=false`, which keeps them exactly as typed ("gym").

Date ranges become all-day events marked **Free**, so a trip shows where you are without blocking anything or triggering clash warnings.

## Choosing a calendar (optional)

If you colour-code with several calendars, set `PICK_CALENDAR=true`. Then:
- Add a tag to send it straight to a calendar: `Tutorial thurs 10-12pm #school`. Tags ignore case and spaces, and a short start works if it's unique (`#sch`, `#extra` for EXTRA SCHOOL).
- No tag (or one that matches nothing, or several calendars): the bot shows a button for each calendar.

```
You:  dinner w ash fri 7pm
Bot:  📅 dinner w ash · Fri 20 Nov, 7pm to 8pm
      Which calendar?
      [DELS] [SCHOOL] [TUITION] [WORKOUT] [WORK] … [Cancel]
```

`/start` lists your calendars as tags, read live from iCloud, so it stays right when you add or rename one (send `/refresh` first so the bot sees the change).

Leave it `false` to send everything to `CALENDAR_NAME`, exactly as before. `CALENDAR_NAME` must still be a real calendar name either way, since it's the fallback.

## Deleting events

Send `delete` plus part of the title, e.g. `delete footie` (also works with `remove`, `cancel` or `/delete`). Add a date if there are many matches: `delete footie 12/11`. Plain `delete` lists the next 2 weeks.

The bot shows matching events as buttons. Nothing is removed until you confirm:
- One-off event: **Yes, delete** or **Keep it**
- Repeating event (🔁): **Only <that date>**, **Stop repeating from here** (that date and every later one go, earlier ones stay), or **Keep it**

Commands: `/where` (or `/where 18 dec`) tells you which trip you're on that day, `/today`, `/tomorrow`, `/week` (7 days) and `/month` (30 days) list what's on, `/day 18 dec` (or shortcuts like `/18dec`, `/fri`, `/16-21dec`) shows a specific day or range, with any trip at the top, `/undo` deletes the last event the bot added, `/refresh` reconnects to iCloud (use it if the bot seems stuck, or after adding a calendar).

Clash checks look at every calendar on your account (or only those in `CHECK_CALENDARS`). For repeating events it checks the next 3 months. Events marked "Free" and all-day events are ignored unless you turn `ALL_DAY_COUNTS_AS_CONFLICT` on.

## New-event alerts

Every `WATCH_MINUTES` minutes (default 5) the bot checks your calendars. When something appears that you didn't add through the bot (an interview invite accepted from an email, an event someone shares with you), it messages you with the details and any clashes. It also tells you when an event is moved or removed. The first check after a restart only takes a snapshot, so you won't get a flood of alerts.

Set `NOTIFY_CHAT_ID` (the bot shows yours when you send `/start`) so alerts keep working after restarts. Without it, alerts start once you've messaged the bot.

Don't need alerts? Set `WATCH_MINUTES=0`. Adding, deleting and clash checks still work, `/start` stops mentioning alerts, and the bot does less work (cheaper on hosts that bill by usage).

**Google Calendar (optional):** to include a Google calendar in alerts and clash checks, open Google Calendar on the web, go to Settings, pick the calendar, copy **Secret address in iCal format**, and set `EXTRA_ICS_URLS=Google|<that link>`. Google events then count exactly like Apple ones (shown in lists, alerts and clash checks, always as Busy, even though Gmail marks its automatic events as Free). It's read-only, so delete or edit them in Google, and Google can take a while to update that link.

## Setup (about 10 minutes)

**1. Create the bot.** In Telegram, message **@BotFather**, send `/newbot`, pick a name, and copy the token.

**2. Lock it to you.** Message **@userinfobot** and put the number it gives you in `ALLOWED_TELEGRAM_IDS`. (A username in `ALLOWED_TELEGRAM_USERNAMES` also works, but an ID can't be changed or taken by someone else.) **If both are left blank, anyone who finds the bot can use your calendar.**

**3. Make an Apple app-specific password.** Go to account.apple.com, Sign-In and Security, App-Specific Passwords, and generate one (e.g. "Telegram calendar"). Your normal Apple password won't work here, and you can revoke this one any time.

**4. Configure.**
```bash
cp .env.example .env
# fill in the token, your ID, Apple ID email, app password, and calendar name
```

| Setting | What it does |
|---|---|
| `TELEGRAM_BOT_TOKEN` | From @BotFather. **Required** |
| `ALLOWED_TELEGRAM_IDS` / `ALLOWED_TELEGRAM_USERNAMES` | Who may use the bot. **Set one** |
| `APPLE_ID` | Your Apple ID email. **Required** |
| `APPLE_APP_PASSWORD` | App-specific password, `xxxx-xxxx-xxxx-xxxx`. **Required** |
| `CALENDAR_NAME` | Default calendar, exactly as named in the Calendar app (blank = first one) |
| `PICK_CALENDAR` | `true` = choose a calendar per event with `#tags` or buttons. Default `false` |
| `CAPITALISE_TITLES` | `false` = keep titles as typed ("gym"). Default `true` ("Gym") |
| `CHECK_CALENDARS` | Only check these calendars for clashes, comma-separated (blank = all) |
| `ALL_DAY_COUNTS_AS_CONFLICT` | Count all-day events as clashes. Default `false` |
| `TIMEZONE` | e.g. `Asia/Singapore` |
| `WATCH_MINUTES` | How often to check for new events. `0` turns alerts off. Default `5` |
| `NOTIFY_CHAT_ID` | Where alerts go after a restart (shown on `/start`) |
| `EXTRA_ICS_URLS` | Read-only extra calendars, e.g. Google (see above) |
| `ICLOUD_TIMEOUT` | Seconds to wait for iCloud before giving up. Default `45` |

**5. Run.**
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python bot.py
```
Then open your bot in Telegram and send `/start`.

## Keeping it running

The bot only works while `python bot.py` is running somewhere.

- **Your Mac:** fine for trying it out, but it stops when the Mac sleeps.
- **A small always-on host:** any service that runs a Docker container works (a cheap VPS, Railway, Fly.io, or a Raspberry Pi at home). Use the included `Dockerfile` and set the `.env` values as environment variables. It uses polling, so no web address or webhook is needed.

**Only run one copy per bot token.** If it's running on a host, stop the local one (Ctrl+C), or Telegram splits messages between them and you'll see `Conflict: terminated by other getUpdates request` in the logs.

### Railway

1. Push your code to GitHub.
2. railway.com → **Login with GitHub** → **New Project** → **Deploy from GitHub repo** → pick this repo. The first build crashes because it has no settings yet. That's expected.
3. Click the service → **Variables** → **Raw Editor** → paste the contents of your `.env` → **Update Variables** → **Deploy**.
4. Send `/start` to your bot. Logs are under **Deployments → View logs**.

Every push to GitHub redeploys automatically. Railway's `.env` is the Variables screen: it never reads the `.env` file on your computer, so change settings in both places.

**Cost:** Railway bills by usage, mostly memory (the bot is idle but running 24/7). One bot uses roughly $0.60–1 a month, which is around the Free plan's $1 monthly credit. To keep it down: set `WATCH_MINUTES=0` if you don't need alerts, add `MALLOC_ARENA_MAX=2` (a standard trick that lowers Python's memory use), keep it to one service, and check **Usage** after the first week. Without a card on file you can't be charged; the bot just stops until the credit resets. Hobby ($5/month incl. $5 usage) fits two bots comfortably.

## Setting it up for someone else

Each person needs their **own** bot, because the bot writes to whichever Apple account is in its settings. Same code, different settings:

1. They fork this repo on GitHub (or you deploy it for them).
2. They make their own bot with @BotFather, get their ID from @userinfobot, and create their own app-specific password.
3. They deploy their fork (e.g. their own Railway account, so each person gets their own free credit) and paste **their** values into Variables.

Every setting has a sensible default, so leaving `PICK_CALENDAR` and `CAPITALISE_TITLES` out gives them the plain version. Don't add their ID to your bot: that would let them read and edit your calendar. When you improve your repo, they click **Sync fork** on GitHub to get the changes.

## Troubleshooting

| What you see | Fix |
|---|---|
| Bot says "Saved" but it's not on your iPhone | It's in iCloud; your phone hasn't fetched it. Open Calendar and pull down to refresh. For automatic updates: Settings → Calendar → Accounts → Fetch New Data → Push on, and turn off Low Power Mode |
| Bot stuck on "Checking your calendar…" or not replying | Send `/refresh`. If nothing answers at all, restart the service (Railway → Deployments → ⋮ → Restart) |
| "iCloud didn't answer in time" | iCloud was slow. Send the message again; the bot reconnects on its own |
| `401 Unauthorized` in the logs | Wrong Apple ID email or app password (use the email, not a phone number) |
| "Calendar 'X' not found" | `CALENDAR_NAME` must match a calendar name exactly |
| `Conflict: terminated by other getUpdates request` | Two copies are running with the same token. Stop one |
| Bot ignores you | Your ID isn't in `ALLOWED_TELEGRAM_IDS`, or the bot isn't running |

## Security

The app-specific password can read your iCloud calendars and contacts, so keep `.env` private (it's in `.gitignore`) and keep `ALLOWED_TELEGRAM_IDS` (or `ALLOWED_TELEGRAM_USERNAMES`) set. If anything leaks, revoke the password at account.apple.com and the bot token with `/revoke` in @BotFather, then update your settings.

## Tests

```bash
pip install pytest && python -m pytest tests
```
