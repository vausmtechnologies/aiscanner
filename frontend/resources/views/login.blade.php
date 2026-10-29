<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Login - AI Document Scanner</title>
<style>
  * { box-sizing: border-box; }
  body { margin: 0; min-height: 100vh; display: grid; place-items: center; background: linear-gradient(180deg, #e8f1ff, #f2f7ff); color: #0f2540; font: 15px/1.55 system-ui, sans-serif; }
  form { background: #fff; border: 1px solid #dce8f7; border-radius: 18px; padding: 28px; width: min(360px, 92vw); box-shadow: 0 8px 24px rgba(37,99,235,.08); }
  h1 { margin: 0 0 16px; font-size: 20px; }
  input { width: 100%; padding: 11px 14px; border: 1px solid #dce8f7; border-radius: 12px; font: inherit; margin-bottom: 12px; }
  button { width: 100%; background: #2563eb; color: #fff; border: 0; border-radius: 12px; padding: 11px; font: inherit; font-weight: 600; cursor: pointer; }
  .err { color: #b91c1c; margin: 0 0 10px; font-size: 14px; }
</style>
</head>
<body>
<form method="POST" action="{{ route('login.store') }}">
  @csrf
  <h1>AI Document Scanner</h1>
  @error('password')<p class="err">{{ $message }}</p>@enderror
  <input type="password" name="password" placeholder="Password" autofocus required>
  <button type="submit">Login</button>
</form>
</body>
</html>
