# git-authors

## Introduction
Once a year, we need to generate some stats on the various ID repos to help get a tax credit for R&D (talk to Eli if you want real information about this).
This repo should help make it easier on you than trying to gather stats manually.
It clones all of our repos to a temp folder (so you don't have to have them clutter your repo directory), generates the stats we need, and cleans up after itself like a good program.

## How to use
- Go to [https://github.com/settings/tokens](https://github.com/settings/tokens) and generate a "personal access token" with the permission of `repo`.
- Run the tool like `python dive_authors.py --access-token={} --year={} --outfile={}`.
  - `--access-token` is required and will be the token that you generated in the above step
  - `--year` will default to the previous year (if it is 2019, the tool will run for 2018)
  - `--outfile` will default to `git-stats.csv`

