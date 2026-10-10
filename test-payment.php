<?php
session_start();

// Generate a dummy token (simulate what PayFast would return)
$token = bin2hex(random_bytes(32));
$_SESSION['download_token'] = $token;
$_SESSION['selected_cover'] = 'cover1'; // or whichever you want

// Redirect to the success page with the token
header("Location: success.html?token=" . $token);
exit;
?>
