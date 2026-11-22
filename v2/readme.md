# TrekHub v2

A trekking management web application built with **Flask** and **Bootstrap**. Version 2 adds online payments using **Razorpay (Test Mode)** and stronger token-based security (JWS).

---

## Table of Contents

1. [Features](#features)
2. [Tech Stack](#tech-stack)
3. [Project Structure](#project-structure)
4. [Installation](#installation)
5. [Configuration](#configuration)
6. [Running the App](#running-the-app)
7. [Razorpay Integration (Test Mode)](#razorpay-integration-test-mode)
8. [Troubleshooting](#troubleshooting)

---

## Features

- User registration and login
- Browse treks and make bookings
- Online payment for bookings using Razorpay Test Mode
- Token-based authentication (JWS)
- Responsive UI using Bootstrap

## Tech Stack

| Layer    | Technology                                     |
| -------- | ---------------------------------------------- |
| Backend  | Python, Flask                                  |
| Frontend | HTML (Jinja2 templates), Bootstrap             |
| Payments | Razorpay (Python SDK + Checkout.js), Test Mode |
| Auth     | JWS-based tokens                               |

## Project Structure

```
v2/
├── app.py               # Flask application entry point
├── config.py            # All configuration (secrets, database, Razorpay keys)
├── requirements.txt     # Python dependencies
├── templates/           # HTML templates
└── static/              # CSS, JS, images
```

> Update this to match your actual `v2/` folder.

## Installation

```bash
git clone https://github.com/princemunjal365/TrekHub.git
cd TrekHub/v2
pip install -r requirements.txt
```

## Configuration

Everything is configured in `config.py`. Set these values before running:

```python
SECRET_KEY = "your-secret-key"

# Razorpay Test Mode keys
RAZORPAY_KEY_ID = "rzp_test_xxxxxxxxxxxx"
RAZORPAY_KEY_SECRET = "your-test-key-secret"
```

## Running the App

```bash
python app.py
```

Open `http://127.0.0.1:5000` in your browser.

---

## Razorpay Integration (Test Mode)

This project uses Razorpay in **Test Mode**, so no real money is charged and no KYC is needed.

### How it works

1. User clicks **Pay** on a booking.
2. The Flask backend creates a Razorpay **order**.
3. The browser opens the Razorpay **Checkout** popup using that order.
4. After payment, Razorpay returns a payment ID and signature.
5. The backend **verifies the signature** and marks the booking as paid.

### Step 1: Get test API keys

1. Create an account at [razorpay.com](https://razorpay.com) and log in to the Dashboard.
2. Make sure **Test Mode** is switched on (toggle at the top).
3. Go to **Account & Settings → API Keys → Generate Key**.
4. Copy the **Key ID** (starts with `rzp_test_`) and **Key Secret** into `config.py`.

The Key Secret is shown only once, so save it somewhere safe.

### Step 2: Install the SDK

```bash
pip install razorpay
```

## Troubleshooting

| Problem                      | Likely cause                                                  |
| ---------------------------- | ------------------------------------------------------------- |
| `Authentication failed`      | Wrong Key ID or Secret, or a live key mixed with a test key   |
| Signature verification fails | Wrong Key Secret, or the three fields were not sent correctly |
| Invalid amount error         | Amount is not in paise or is a decimal                        |
| Checkout popup does not open | `checkout.js` not loaded, or `order_id` / `key` missing       |
| `ModuleNotFoundError`        | Run `pip install -r requirements.txt`                         |

---

## Author

Prince Munjal, [github.com/princemunjal365](https://github.com/princemunjal365)
