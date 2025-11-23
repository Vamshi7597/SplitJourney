# How to Use SplitJourney on Mobile (Free)

Since SplitJourney is built with Flet (Python), the easiest way to use it on your mobile for free is to **deploy it as a Web App**.

## The Concept: Central Server
To allow 4 members to see the same data:
1.  The **App** runs on a server (Render).
2.  The **Data** lives in a shared cloud database (Neon/Postgres).
3.  **Everyone** accesses the **same URL** (e.g., `https://splitjourney.onrender.com`) from their own phones.
4.  When you add an expense, it saves to the cloud database. When your friend refreshes their page, they see it instantly.

---

## Step-by-Step Deployment Guide

### Phase 1: Get a Free Cloud Database (Required for Data Sync)
Since Render's free servers reset (wiping local files), you need a separate database.
1.  Go to **[Neon.tech](https://neon.tech)** (Free Postgres Database).
2.  Sign up and create a project (e.g., "SplitJourney").
3.  Copy the **Connection String** (it looks like `postgresql://user:pass@...`).
    *   *Tip: Select "Pooled connection" if available, or just the standard one.*

### Phase 2: Deploy the App to Render
1.  **Push your code to GitHub**:
    *   Create a repository on GitHub.
    *   Push your `SplitJourney` code there.
2.  **Sign up on [Render.com](https://render.com)**.
3.  **Create a Web Service**:
    *   Click "New +" -> "Web Service".
    *   Connect your GitHub repository.
    *   **Runtime**: Python 3
    *   **Build Command**: `pip install -r requirements.txt`
    *   **Start Command**: `flet run main.py --port $PORT`
4.  **Environment Variables** (Crucial Step):
    *   Scroll down to "Environment Variables" and add these:
        *   `PYTHON_VERSION`: `3.9.0`
        *   `GOOGLE_PLACES_API_KEY`: (Your Google API Key)
        *   `DATABASE_URL`: (Paste the Neon Connection String from Phase 1)
            *   *Note: If the string starts with `postgres://`, change it to `postgresql://`*

### Phase 3: Share with Friends
1.  Once Render finishes building, it will give you a URL (e.g., `https://splitjourney.onrender.com`).
2.  **Send this URL to your 3 friends.**
3.  Everyone opens it in Chrome/Safari on their phones.
4.  **Sign Up**: Each person should create their own account (Sign Up -> Enter Name/Email).
5.  **Create Group**: One person creates the "Trip Group" and adds the others.
6.  **Done!** Now everyone can add expenses and see the balance updates in real-time.

## Option 2: Run Locally (Same Wi-Fi) - No Internet Required
If you are all in the same house/hotel on the same Wi-Fi:
1.  Find your laptop's IP address (e.g., `192.168.1.5`).
2.  Run: `flet run main.py --port 8550 --view web_browser`
3.  Tell friends to visit `http://192.168.1.5:8550` on their phones.
4.  *Limitation:* Only works while your laptop is ON and running the app.

## ✅ Pre-Trip Checklist (Laptop Independence)
**Do this BEFORE you leave your laptop behind:**

1.  [ ] **Deploy to Render**: Ensure the status is "Live" (Green).
2.  [ ] **Test on Phone**: Turn OFF your laptop's Wi-Fi. Open the Render URL on your phone.
3.  [ ] **Verify Data**: Add a test expense on your phone.
4.  [ ] **Share URL**: Send the link to your friends.

**Once these 4 steps are done, you DO NOT need your laptop.** The app is now living in the cloud (Render + Neon). Have a great trip! ✈️
