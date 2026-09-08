# DeepSeek + OpenCode Session Log – 2026-09-06 to 2026-09-08

## 1. Book Publishing Metadata Finalised
- Title: Renaissance of the Poor Soul
- Subtitle: A journey through the many faces of the human spirit
- Author: Halalisani Ngema
- Imprint Publisher: Liviyo Press
- Edition: First Edition
- Print ISBN: 978-1-0492-8328-9
- Ebook ISBN: 978-1-0492-8329-6
- Price: R140 (ZAR)
- Website: renaissance.liviyo.co.za

## 2. SSH Key Setup – Passwordless Sync
- dom: win@100.108.245.14
- gui: liviyo@100.83.171.72
- Steps: generated key, ssh-copy-id, tested – works passwordless.

## 3. Full Site Sync (dom → gui)
- rsync command with excludes.
- Synced: bizroad, jobs_careerwins, jobs_future-flow, jobs_jobsani, liviyo_capital, liviyo_media, jobs_renaissance.

## 4. Sync Script Created
- /home/win/bin/sync-all-sites.sh
- Alias: sync-all

## 5. Cron Prepared (not activated)
- Hourly and 15-minute schedules.

## 6. Lulu Guide Saved
- /home/win/Desktop/lulu.txt

## 7. Tailscale & SSH Troubleshooting
- Relay latency >1300 ms; workaround via Tailscale app SSH.

## 8. GA/GTM Cleanup Plan
- Single GA4 property and GTM container for all subdomains.

## 9. Outstanding SEO Tasks
- Amazon/Gumroad links still placeholders.
- Sitemaps not submitted for capital, media, bizroad.
- GA4 not installed.
- Social accounts not verified.

## 10. Renaissance Site Live Status
- Design, blog, author photo, legal pages live.
- Buy buttons: Lulu added, Amazon removed.
- Kit (ConvertKit) email signup form added (script embed).

## 11. Buy Section Design Fixes
- Cards resized, scroll-margin-top fixed.
- Lulu logos placed at top of each card.
- Gold placeholders removed.

## 12. PayFast Direct Sales Integration
- Merchant ID: 34944543
- Merchant Key: hg2amrkziqu6v
- Price: R140
- Files: /assets/direct_book/PDF/ (5 cover variants)
- Need checkout page with cover thumbnails, secure payment, and protected download.

## 13. Next Steps for Codespaces
- Build /checkout.html with cover selection.
- Integrate PayFast form with secure badge.
- Implement protected download after payment.
- Add HTTPS and security measures.

## 14. Paths and IPs Reference
| Item | Value |
|------|-------|
| dom | 100.108.245.14 |
| gui | 100.83.171.72 |
| Book path (dom) | /home/win/liviyo_pc/job/websites/liviyo_capital/working_sites/jobs_renaissance/ |
| Book path (gui) | /home/liviyo/Documents/job/websites/liviyo_capital/working_sites/jobs_renaissance/ |

