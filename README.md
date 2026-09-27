# job_pull

Pulls new Platsbanken (Swedish job board) ads every 3 days for a fixed set
of search terms, via Arbetsförmedlingen's free, keyless JobTech JobSearch
API. New ads land in `jobs/ads_<date>.json`; `state.json` tracks what's
already been seen so nothing repeats.

Runs on a GitHub Actions schedule (see `.github/workflows/schedule.yml`).
Can also be triggered manually from the Actions tab ("Run workflow").
