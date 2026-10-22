// Key-hiding proxy: browser -> this server (no key) -> Laravel API (X-API-Key added here).
// Zero dependencies, Node 18+. Run: API_KEY=... node server.js
const http = require('http');
const { URL } = require('url');

const TARGET = new URL(process.env.API_URL || 'http://127.0.0.1:8001');
const API_KEY = process.env.API_KEY || '';
const PORT = Number(process.env.PORT || 3001);
const ALLOWED_ORIGIN = process.env.ALLOWED_ORIGIN || 'http://localhost:3000';

// Only the routes the frontend needs; everything else is refused.
const ALLOWED = [
  ['POST', /^\/api\/scan$/],
  ['GET', /^\/api\/scan\/[^/]+\/(status|result)$/],
  ['GET', /^\/api\/search$/],
];

if (!API_KEY) {
  console.error('API_KEY is required (same value as API_KEY in frontend/.env).');
  process.exit(1);
}

http.createServer((req, res) => {
  res.setHeader('Access-Control-Allow-Origin', ALLOWED_ORIGIN);
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  if (req.method === 'OPTIONS') return res.writeHead(204).end();

  const path = req.url.split('?')[0];
  if (!ALLOWED.some(([m, re]) => m === req.method && re.test(path))) {
    return res.writeHead(404, { 'Content-Type': 'application/json' }).end('{"message":"Not found"}');
  }

  const headers = { ...req.headers, host: TARGET.host, 'x-api-key': API_KEY };
  delete headers.origin;

  const upstream = http.request(
    {
      hostname: TARGET.hostname,
      port: TARGET.port,
      path: req.url,
      method: req.method,
      headers,
    },
    (up) => {
      res.writeHead(up.statusCode, up.headers);
      up.pipe(res);
    },
  );
  upstream.on('error', () => res.writeHead(502).end('{"message":"Upstream unreachable"}'));
  req.pipe(upstream); // streams uploads (multipart/zip) without buffering
}).listen(PORT, () => console.log(`Proxy on :${PORT} -> ${TARGET.href}`));
