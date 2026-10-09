# Profile README setup

This directory is ready to become the public `dastanalseit/dastanalseit` repository. Its root `README.md` is the profile page. The images are committed SVGs, so they remain visible between updates.

- `profile.json`: text on the info card. Edit it, then run `python3 scripts/profile_art.py card`.
- `assets/avatar.pgm`: a small grayscale version of the current public GitHub avatar. Run `python3 scripts/profile_art.py portrait` after replacing it.
- `data/contributions.json`: snapshot of the public contribution graph. Run `python3 scripts/profile_art.py fetch` and `python3 scripts/profile_art.py heatmap` to refresh it locally.
- `.github/workflows/update-profile-art.yml`: refreshes the graph daily at 06:17 UTC and on manual dispatch. GitHub Actions needs repository Actions enabled and the `GITHUB_TOKEN` allowed to write repository contents.

No third-party Python packages or personal access token are required for daily updates. The public GitHub contributions HTML is an undocumented source; if GitHub changes its markup, the job fails instead of writing an empty graph.

The portrait uses the current public GitHub avatar. To replace it with a photo, export the image as an 84×52 pixel grayscale ASCII PGM (`P2`) file at `assets/avatar.pgm`, then run the portrait command.
