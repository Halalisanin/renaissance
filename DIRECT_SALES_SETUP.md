# Direct book sales deployment

The checkout frontend is static, but secure delivery requires PHP 8+, HTTPS, cURL, and a writable directory outside the public web root.

## Private files

Create `/home/liviyo/private_book_delivery` on the server with mode `0700` and place these files inside it:

```text
cover1.pdf
cover2.pdf
cover3.pdf
cover4.pdf
cover5.pdf
```

Place matching first-page JPEG thumbnails in `assets/direct_book/thumbnails/` and run `tools/extract_direct_book_thumbnails.sh` after copying the source PDFs into `assets/direct_book/PDF/`. Do not commit PDFs or the private delivery directory.

## Environment

Set `RENAISSANCE_DOWNLOAD_SECRET` to a long random value. Set `PAYFAST_PASSPHRASE` to the passphrase configured in the PayFast merchant account. `notify.php` rejects requests unless the private directory and download secret exist, verifies the PayFast signature, then validates the complete POST with PayFast over TLS before recording the order.

Use PayFast sandbox credentials and sandbox endpoints in a separate deployment before switching the form to live credentials. The live form currently posts to `https://www.payfast.co.za/eng/process`.

## Hosting requirement

GitHub Pages and other static-only hosting cannot run `notify.php` or `download.php`; deploy these files to PHP hosting under the same HTTPS domain, or move the handlers to a separate HTTPS backend and update the form URLs. Do not place the PDFs under the public document root.