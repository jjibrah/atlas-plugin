# Go-live checklist — {{Project name}} — {{P1}}

<!-- SENTINEL. Every item is a "- [ ]" checkbox; Spartan's G5 counts unchecked ones. Tick "- [x]" only when the
     user confirms it is done. Scale to size: Small → keep only what applies (often 8–12 items). Remove sections that
     truly do not apply (say why in one line). "Rollback" is required when a Critical module is in the phase.
     Never write secrets, passwords or keys here — only WHERE they are configured. -->

Owner: {{name/role}} · Planned go-live: {{date and time}} · Release: {{version / tag}}

## Environments
- [ ] Production environment exists and matches staging ({{hosting provider}})
- [ ] Domain / DNS and HTTPS certificate in place
- [ ] Final build deployed to staging and smoke-tested

## Data and backups
- [ ] Backup of production data taken and a restore tested
- [ ] Data migration rehearsed on a copy of real data; record counts match ({{or: no migration in this phase}})

## Configuration and secrets
- [ ] All configuration and secrets set in {{hosting provider}} environment settings (none in files or the repo)
- [ ] Third-party accounts switched from test to live mode ({{payments, email, …}})

## Monitoring and alerts
- [ ] Error tracking and uptime check active; alerts go to {{who}}
- [ ] Logs reachable, with no personal data or secrets written to them

## Rollback
- [ ] Rollback trigger agreed: {{e.g. checkout failing for more than 10 minutes}}
- [ ] Rollback steps written: {{redeploy previous release / restore backup / switch flag off}}
- [ ] Rollback rehearsed on staging (date: {{…}})

## Support and handover
- [ ] Owner for the first week named; support contact shared with the client
- [ ] Admin access handed to the client; shared credentials rotated

## Communication
- [ ] Users told what changes and when ({{channel}})
- [ ] Client confirms go-live time
