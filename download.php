<?php
declare(strict_types=1);
require __DIR__ . '/payfast-config.php';

if ($_SERVER['REQUEST_METHOD'] !== 'GET' || !delivery_configured()) fail_request(404, 'Not found');
$referer = (string) ($_SERVER['HTTP_REFERER'] ?? '');
if (!preg_match('#^https://renaissance\.liviyo\.co\.za/success\.html(?:\?|$)#', $referer)) fail_request(403, 'Download must be started from the confirmation page');
$token = (string) ($_GET['token'] ?? '');
if (isset($_GET['action']) && $_GET['action'] === 'token') {
	$paymentId = (string) ($_GET['payment_id'] ?? '');
	if (!valid_payment_id($paymentId)) fail_request(400, 'Invalid payment request');
	$record = read_payment($paymentId);
	if (!$record || ($record['payment_status'] ?? '') !== 'COMPLETE') fail_request(403, 'Payment confirmation pending');
	$issuedToken = issue_download_token($paymentId);
	if ($issuedToken === null) fail_request(503, 'Download service unavailable');
	header('Content-Type: application/json; charset=UTF-8');
	header('Cache-Control: no-store');
	echo json_encode(['token' => $issuedToken]);
	exit;
}
$paymentId = consume_download_token($token);
if ($paymentId === null || !valid_payment_id($paymentId)) fail_request(403, 'Invalid or expired download token');
$record = read_payment($paymentId);
if (!$record || ($record['payment_status'] ?? '') !== 'COMPLETE') fail_request(403, 'Payment confirmation pending');
$cover = $record['cover'] ?? '';
if (!preg_match('/^cover[1-5]$/', $cover)) fail_request(403, 'Invalid cover');
$file = DELIVERY_ROOT . '/' . $cover . '.pdf';
if (!is_file($file) || !is_readable($file)) fail_request(404, 'The selected book file is not available');
header('Content-Type: application/pdf');
header('Content-Disposition: attachment; filename="renaissance-of-the-poor-soul-' . $cover . '.pdf"');
header('Content-Length: ' . (string) filesize($file));
header('Cache-Control: private, no-store');
readfile($file);