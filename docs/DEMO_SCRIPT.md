# Demo script (2 – 3 minutes)

A timed walkthrough for the screen recording. Speak naturally; the lines in *italics* are suggestions, not a script to memorise.

## Before you press record (2 minutes)

1. **Fresh data.** Stop the backend, delete `backend/leadflow.db`, start the backend again (the admin is recreated automatically).
2. **Both servers running** — `scripts\start-dev.ps1`, or the two commands in the README.
3. **Keys in place** — `GROQ_API_KEY` and/or `GEMINI_API_KEY` in `backend/.env`. Quick check: open http://localhost:8000/docs.
4. *(Optional, makes the dashboard richer)* run `backend\.venv\Scripts\python scripts\seed_demo_data.py --statuses` and wait for it to finish, then leave 1–2 enquiries for the live part. Keep the first sample, the assignment's own example, **unused** so you can submit it live.
5. **Screen:** browser window 1366×768 or larger, zoom 100%, close other tabs and notifications. Have two tabs: `http://localhost:5173/` and `http://localhost:5173/admin/login`.
6. Do one dry run — the AI needs 5–15 seconds per enquiry.

## Timeline

| Time | Show | Say |
|---|---|---|
| **0:00 – 0:15** | Customer site `http://localhost:5173/` | *"This is LeadFlow, an AI workflow for customer enquiries at Kiwi Connect Digital. Customers get a simple public site; the team gets an admin console."* |
| **0:15 – 0:45** | Scroll to the form and submit the assignment example: *"I own a clothing store in Indore. I need an e-commerce website where customers can browse products, place orders and make online payments. My budget is around ₹50,000."* (use a fictional name/phone/email) | *"The customer only sees a thank-you with a reference number. Behind the scenes the backend saved the original, assigned an owner and started the AI workflow."* |
| **0:45 – 1:05** | Admin login → **Overview** | *"Here's the dashboard: total, new, high-priority, in-progress and converted enquiries, category distribution, lead temperature, growth over time."* |
| **1:05 – 1:50** | **Enquiries** → open the new enquiry | *"On the left is the original message, untouched. The AI extracted the category, E-commerce Development, budget ₹50,000, location Indore, the requirements, and what's missing."* Point to **missing information**, then the **lead score ring and breakdown** (*"computed by rules, not guessed by the AI, with an explanation"*), then the **priority reason**. |
| **1:50 – 2:10** | Scroll to **Suggested customer response** → edit a sentence → **Save response** → click **Use AI original** | *"The AI drafted a professional reply with follow-up questions. The admin can edit it; the original AI draft is always kept."* Change status to **In Progress**. |
| **2:10 – 2:30** | **Workflow History** for that enquiry | *"Every step of the automation is logged with timings — duplicate check, extraction, classification, priority, scoring, reply, assignment, email alert. If the AI fails, the enquiry is kept and can be retried."* |
| **2:30 – 2:50** | Quick tour: **Enquiries** filters/search + **Excel** export → **Follow-ups** → **Team** → **AI Monitoring** | *"Bonus features: duplicate detection, lead scoring, follow-up reminders, auto-assignment to team members, WhatsApp and email, CSV and Excel export, analytics, and AI usage monitoring."* |
| **2:50 – 3:00** | Back to the customer site or the dashboard | *"Python FastAPI, React, SQLite, and Groq with a Gemini fallback. Thanks for watching."* |

## If something goes wrong during the recording

- **"AI failed" on the live enquiry** — that is a free-tier rate limit; open the enquiry, press **Retry analysis**, and narrate it: *"if the AI is unavailable the enquiry is preserved and can be retried"*. It is a feature worth showing.
- **Page is blank** — stop `npm run dev`, delete `frontend/node_modules/.vite`, start it again.
- **Slow** — seed the data *before* recording, and only submit one enquiry live.

## Optional extras if you have time (+15 s each)

- Submit the Hindi sample (`मुझे अपनी दुकान के लिए वेबसाइट चाहिए…`) to show multilingual handling and a Hindi reply.
- Submit the same email twice to show the **duplicate warning**.
- Open the **prompt-injection** sample to show *Needs review* and a low score.
- Click **WhatsApp** on an enquiry to show the pre-filled chat link.
