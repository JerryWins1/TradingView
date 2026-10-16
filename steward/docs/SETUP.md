# Steward setup checklist

Everything below is a one-time step for Jerry. Nothing here moves real money.
Each step is independent; do them in any order, and tell Claude when one is
done so the next piece can be switched on.

## 1. Give Steward its own home (5 minutes)

1. Go to https://github.com/new
2. Repository name: `steward`. Visibility: **Private**. Tick **Add a README file**. Create.
3. If GitHub asks which repositories the Claude app may access, add `steward`.
4. Tell Claude "repo is up." Claude moves the code over from the TradingView backup branch and closes that PR.

Then turn on the dashboard web page: repo **Settings → Pages → Source: Deploy from a branch → Branch `main`, folder `/docs`**. The URL will be `https://jerrywins1.github.io/steward/`.

## 2. Open the Alpaca paper account (5 minutes)

1. https://alpaca.markets → Sign up → choose the **paper trading** account (skip the live account).
2. In the paper dashboard, use **Reset** to set the balance to **$25,000**.
3. Generate an **API key** and **secret** (paper keys start with `PK`).
4. In the `steward` repo: **Settings → Secrets and variables → Actions → New repository secret**:
   - `ALPACA_API_KEY` = the key
   - `ALPACA_SECRET_KEY` = the secret
5. **Actions → Weekly check-in → Run workflow** with **dry run** ticked. Read the orders it would place. Run again without dry run only when you are happy.

From then on it runs every Monday at about 10:40am Eastern and emails you the check-in as a GitHub issue.

## 3. Apply for Schwab API access (10 minutes now, 1 to 3 business days of waiting)

This is for the real-money path later. It costs nothing to apply now.

1. https://developer.schwab.com → **Register** a developer account (status goes to "pending review").
2. When approved, open **Products** and request **Trader API – Individual**.
3. Create an **App**: name it anything, callback URL `https://127.0.0.1:8182`, product Trader API – Individual.
4. Note the **App Key** and **App Secret**. Keep them private. Later they go in GitHub secrets `SCHWAB_APP_KEY` and `SCHWAB_APP_SECRET`, and on your computer for the weekly login.

The weekly login (Schwab's 7-day rule): on your own computer, run
`python -m steward schwab login-url`, open the link, approve, and paste the
URL you land on into `python -m steward schwab login <that url>`. The system
then has a week of access.

## 4. Fill in your tax assumptions (2 minutes, private)

Edit `[tax]` in `rules.toml` in the private repo (not in chat):

- `account_type = "taxable"` (already set)
- `ordinary_rate`: your federal bracket for ordinary income
- `long_term_rate`: 0.00, 0.15 or 0.20 by your taxable income
- `state_rate`: your state's rate on capital gains, if any
- `niit = true` if MAGI is over $200k single / $250k joint

The 2026 thresholds are in `brain/state.md` under "Tax facts on file."

## 5. Later, when the paper results have earned it

- Flip `[options] mode` from `"watch"` to `"trade"` after a month of logged spreads look sensible.
- Real money: a $1-size test order through the Schwab adapter first, then `[schwab] live = true`, with every order still approved by you.
