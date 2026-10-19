# Deployment decision — 2026-10-19

**Selected delivery: a working local Docker deployment.** Cloud hosting is
optional, and no hosting subscription, payment method, registry upload, public
endpoint, or external dataset transfer has been created.

## Current options checked against official documentation

| Option | Cost/resource context | Reliability and practical limit |
| --- | --- | --- |
| Local Docker | No additional cloud bill; uses the existing machine, Docker installation, and its resources | Available while the machine and Docker run; localhost access; no public uptime promise |
| Render Free | 0.1 CPU, 512 MB; workspace usage limits apply | Sleeps after 15 idle minutes; about a minute to wake; ephemeral filesystem; free instances are not recommended by Render for production |
| Railway Free | $1 monthly credit; 0.5 GB RAM, one replica, resource caps | Tiny usage allowance is not an always-on guarantee; verify account eligibility and usage before relying on it |
| Railway Hobby | $5/month minimum, including $5 usage; additional usage can increase the bill | More configurable capacity; budget limits and actual resource usage still need checking |

Sources checked October 19, 2026: [Render Free](https://render.com/docs/free),
[Render compute plans](https://render.com/docs/compute-plans),
[Railway plans](https://docs.railway.com/pricing/plans).
These are current published terms, not a promise that hosting stays free.

## Why local is appropriate now

The purpose is to demonstrate a reproducible ML service, not to incur a cloud
bill. The local container runs the real frozen model and aggregate history,
supports interactive API documentation, and can be stopped/restarted. This
satisfies the project's allowed local-deployment alternative while keeping
model/data publication under the account owner's control.

The configured local memory cap is 768 MiB; that is a chosen cap, not a measured
minimum requirement or proof that any free cloud tier has sufficient headroom.
Before a cloud move, measure peak memory during startup and requests, include
cold-start behavior, and check the platform's present terms again.

## Future cloud handoff

After local checks and hosted CI pass, select a host/account and budget. Review
whether to publish the aggregate history and model, distribute a trusted bundle
or image, add authenticated HTTPS ingress and limits, then verify readiness,
prediction consistency, logs, and restart behavior on that host.

The bundle is intentionally ignored by Git. Merely connecting this repository
to a platform will not recreate the model/history automatically. Do not claim
a one-click cloud deployment or expose unauthenticated endpoints prematurely.

See `docker.md` for the fully functional local setup and teardown commands.
