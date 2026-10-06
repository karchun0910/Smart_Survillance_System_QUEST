# Smart Surveillance dashboard

React dashboard for policy rules and detected events. It polls FastAPI every two seconds, so a stored event appears without reloading the page.

## Run

```powershell
Copy-Item .env.example .env
npm.cmd install
npm.cmd run dev
```

Open `http://127.0.0.1:5173`. The default API is `http://127.0.0.1:8000/api/v1` and can be changed with `VITE_API_URL`.

## Missing Lab Coat demonstration

1. Start MySQL and FastAPI, then open this dashboard.
2. Create or enable a rule with observation type `missing_lab_coat`, high severity, the detector's confidence threshold, three visible seconds, and a cooldown.
3. Start the webcam worker and stand without a lab coat for at least three seconds.
4. Wait up to two seconds for **Missing lab coat** to appear under Recent events.
5. Select **Confirm** or **False alarm** and verify that the review badge updates.

If FastAPI or MySQL is unavailable, the dashboard shows an offline warning and keeps retrying. Camera access and the MySQL record still require manual verification on the demonstration computer.

## Checks

```powershell
npm.cmd run lint
npm.cmd run format:check
npm.cmd run build
```
