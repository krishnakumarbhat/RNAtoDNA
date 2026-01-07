# RNAtoDNA

Static (client-side) RNA→DNA PDB converter.

## What it does
- Converts RNA residues to DNA residues inside PDB `ATOM` records (A,C,G,U → DA,DC,DG,DT)
- Optional cleanup:
  - Remove O2' atoms
  - Rename H5 → C7
- Runs fully in your browser (no server, no upload)

## Run locally
Open `public/index.html` in your browser.

## GitHub Pages
This repo includes a GitHub Actions workflow that deploys the `public/` folder to GitHub Pages when you push to the `visual` branch.

1. In GitHub repo settings: Settings → Pages → Build and deployment → Source: **GitHub Actions**
2. Push to `visual`
3. Your site will be available at the Pages URL shown in the Actions run.
