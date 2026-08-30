# RateLab

A multi-tool web app for Chemical Reaction Engineering coursework. Currently has
one working tool — **Order & k Solver** — plus two placeholder modules
(Module 2, Module 3) ready for future assignments.

## What it does

Given time vs. concentration data from a constant-volume batch reactor, it uses
the **integral method** to determine reaction order and rate constant k, for:

- Zero order
- First order
- Second order — unimolecular (2A → P)
- Second order — bimolecular (A + B → P)
- Autocatalytic (A → P, rate = k·C_A·C_P)
- Series (A → B → C, both steps first order)
- Reversible (A ⇌ B, both directions first order)

Two modes:
- **Auto-detect**: tries every model it has enough data for and ranks them by R²
  (closest to 1 wins) — this is the "trial and error" automated.
- **Manual**: you pick the reaction type and it fits just that one.

## Tech stack

- **Backend**: Python (Flask) + NumPy (linear regression / integral-method
  linearization) + SciPy (nonlinear curve fitting, used only for the series
  reaction's k2).
- **Frontend**: plain HTML/CSS/JavaScript + Chart.js (bundled locally in
  `frontend/static/js/vendor/`, no internet/CDN needed at runtime). Light,
  lab-notebook themed UI with a collapsible glossary and a sidebar nav.

## How to run it

```bash
cd backend
pip install -r requirements.txt
python app.py
```

Then open **http://127.0.0.1:5000** in your browser.

(If `pip` complains about externally-managed environments, use
`pip install -r requirements.txt --break-system-packages`, or create a
virtual environment first: `python -m venv venv && source venv/bin/activate`.)

## Folder structure

```
kinetics-lab/
├── backend/
│   ├── app.py                     # Flask app: page routes + /api/predict
│   ├── requirements.txt
│   ├── models/
│   │   ├── fitter.py              # dispatches manual mode / runs auto-detect
│   │   ├── zero_order.py
│   │   ├── first_order.py
│   │   ├── second_order.py        # unimolecular + bimolecular
│   │   ├── autocatalytic.py
│   │   ├── series_reaction.py
│   │   └── reversible_reaction.py
│   └── utils/
│       ├── regression.py          # shared linear-fit + R² helper
│       └── validators.py
└── frontend/
    ├── templates/
    │   ├── base.html              # sidebar + shared layout
    │   ├── index.html             # dashboard / home page
    │   ├── order_predictor.html   # the actual tool
    │   ├── project2.html          # placeholder module
    │   └── project3.html          # placeholder module
    └── static/
        ├── css/style.css
        └── js/
            ├── order_predictor.js # form logic, API calls, Chart.js rendering
            └── vendor/chart.umd.min.js
```

## Adding a new calculator later (Module 2 / Module 3)

1. Add `backend/models/your_model.py` with the math.
2. Wire it into `backend/app.py` with a new route (and into `fitter.py` if it
   belongs in this same tool; otherwise just a standalone route).
3. Build `frontend/templates/project2.html` (or project3.html) using
   `order_predictor.html` as a reference for form + results pattern.
4. Add a matching `frontend/static/js/project2.js` for its form logic.
5. Rename the "Module 2" link text in `frontend/templates/base.html`.

No changes needed to the sidebar structure itself — just relabel and repoint.

## Notes / assumptions baked into the models

- **Bimolecular second order**: assumes 1:1 stoichiometry (A + B → P), so
  `C_B(t) = C_B0 - (C_A0 - C_A(t))`. Requires `C_A0 ≠ C_B0`.
- **Autocatalytic**: requires `C_P0 > 0` (some initial product must be present
  to "kick off" the autocatalysis).
- **Series (A→B→C)**: assumes `C_B0 = 0` (no intermediate present initially).
  k1 comes from a linear fit on C_A data (like first order); k2 is then fit
  nonlinearly (scipy `curve_fit`) against the C_B data with k1 held fixed.
- **Reversible (A⇌B)**: requires the equilibrium concentration `C_Ae` as input
  (read off the plateau of your C_A vs t data). k1 and k2 are separated using
  `K_eq = k1/k2 = C_Be/C_Ae` combined with the fitted `(k1+k2)`.

All seven models were validated against synthetic data generated from their
own analytical solutions with known true k values, and each one recovered the
exact input k (R² = 1.0) before this was shipped.
