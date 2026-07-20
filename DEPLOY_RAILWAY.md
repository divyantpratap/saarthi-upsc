# Deploying Saarthi

This app is a Streamlit RAG service. Below is the Railway path (what you asked for), the two things that need a real decision first, and free alternatives that fit a Streamlit app like this well.

## Read this first: two things to solve before deploy

1. **The knowledge base.** The app is useless without an index to answer from, and the index is not in the repo (the source books are copyrighted, and the built vector store is ~220 MB). Before a public demo works, you need a small, legal knowledge base built from public-domain sources (for example the Constitution of India text plus a few government press releases). That build step produces the `chroma_db/` the deployed app reads from.

2. **Memory.** The default local embedding model pulls in PyTorch, which is heavy (roughly 1 GB of RAM once loaded). Railway's smallest instances can run out of memory on that. Two ways around it:
   - Switch the deployed app to Gemini embeddings (set `EMBEDDING_BACKEND=gemini`), which avoids loading PyTorch entirely and keeps the container light. This is the recommended setting for hosting.
   - Or give the service a plan with enough RAM.

## Option A: Railway (Dockerfile based)

Railway removed its always-free tier, so this runs on a trial credit and then usage-based billing. Fine for a demo, just be aware it is not free forever.

1. Push this repo to GitHub (see the checklist at the bottom).
2. Go to railway.app, sign in with GitHub, and create a new project from your repo.
3. Railway detects the `Dockerfile` and `railway.toml` and builds the image.
4. In the service settings, add environment variables:
   - `GEMINI_API_KEY` = your key
   - `EMBEDDING_BACKEND` = `gemini`   (recommended so the container stays light)
5. Make sure a knowledge base is available (bundle a small public-domain `chroma_db/` in the image, or run the build step as part of deploy).
6. Deploy. Railway gives you a public URL. Put that URL in the README and your GitHub profile.

The Dockerfile already reads Railway's `$PORT`, so no extra config is needed there.

## Option B: Streamlit Community Cloud (free, easiest for this app)

Purpose-built for Streamlit and free for public apps.

1. Push the repo to GitHub.
2. Go to share.streamlit.io, connect the repo, and point it at `app.py`.
3. Add `GEMINI_API_KEY` (and `EMBEDDING_BACKEND=gemini`) under the app's Secrets.
4. Deploy. You get a `*.streamlit.app` URL.

The same knowledge-base note applies: a small public-domain index needs to be present.

## Option C: Hugging Face Spaces (free, more RAM headroom)

Create a Space with the Streamlit SDK, push the repo, and set `GEMINI_API_KEY` as a Space secret. Spaces give a bit more memory room than the smallest Railway/Streamlit tiers, which is handy if you keep the local embedding model.

## Pre-push checklist

- [ ] Confirm `.env` is NOT committed (it holds your API key; it is already in `.gitignore`).
- [ ] Confirm `data/pdfs/` is NOT committed (copyrighted, and 1.6 GB; already in `.gitignore`).
- [ ] Build the small public-domain demo knowledge base for the live demo.
- [ ] Add one screenshot to the README.
- [ ] Fill the live-demo URL into `README.md` and your GitHub profile.
