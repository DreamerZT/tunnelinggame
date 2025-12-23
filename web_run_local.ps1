$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
# 이 스크립트는 "프로젝트 루트" 또는 "build\web" 안 어디서든 실행될 수 있습니다.
if (Test-Path (Join-Path $scriptDir "index.html")) {
  $webRoot = $scriptDir
} else {
  $webRoot = Join-Path $scriptDir "build\web"
}

if (-not (Test-Path (Join-Path $webRoot "index.html"))) {
  Write-Host "❌ build\web\index.html 이 없습니다." -ForegroundColor Red
  Write-Host "먼저 web_build.bat 를 실행해 웹 빌드를 생성해 주세요."
  exit 1
}

function Get-ContentType([string]$path) {
  switch ([IO.Path]::GetExtension($path).ToLowerInvariant()) {
    ".html" { "text/html; charset=utf-8" }
    ".js"   { "text/javascript; charset=utf-8" }
    ".css"  { "text/css; charset=utf-8" }
    ".png"  { "image/png" }
    ".jpg"  { "image/jpeg" }
    ".jpeg" { "image/jpeg" }
    ".gif"  { "image/gif" }
    ".svg"  { "image/svg+xml" }
    ".wasm" { "application/wasm" }
    ".apk"  { "application/octet-stream" }
    default { "application/octet-stream" }
  }
}

function Write-HttpResponse([System.IO.Stream]$stream, [int]$statusCode, [string]$statusText, [string]$contentType, [byte[]]$bodyBytes) {
  $headers = @(
    "HTTP/1.1 $statusCode $statusText",
    "Content-Type: $contentType",
    "Content-Length: $($bodyBytes.Length)",
    # pygame-web(emscripten/threads) 구동에 필요한 CORS/격리 헤더
    "Access-Control-Allow-Origin: *",
    "Cross-Origin-Opener-Policy: same-origin",
    "Cross-Origin-Embedder-Policy: require-corp",
    "Cross-Origin-Resource-Policy: cross-origin",
    "Origin-Agent-Cluster: ?1",
    "Connection: close",
    "",
    ""
  ) -join "`r`n"
  $headerBytes = [Text.Encoding]::ASCII.GetBytes($headers)
  $stream.Write($headerBytes, 0, $headerBytes.Length)
  $stream.Write($bodyBytes, 0, $bodyBytes.Length)
}

function Write-HttpHeadersOnly([System.IO.Stream]$stream, [int]$statusCode, [string]$statusText, [string]$contentType, [int]$contentLength) {
  $headers = @(
    "HTTP/1.1 $statusCode $statusText",
    "Content-Type: $contentType",
    "Content-Length: $contentLength",
    "Access-Control-Allow-Origin: *",
    "Cross-Origin-Opener-Policy: same-origin",
    "Cross-Origin-Embedder-Policy: require-corp",
    "Cross-Origin-Resource-Policy: cross-origin",
    "Origin-Agent-Cluster: ?1",
    "Connection: close",
    "",
    ""
  ) -join "`r`n"
  $headerBytes = [Text.Encoding]::ASCII.GetBytes($headers)
  $stream.Write($headerBytes, 0, $headerBytes.Length)
}

# pygame-web CDN을 로컬 same-origin으로 프록시하기 위한 설정
$remoteCdnBase = "https://pygame-web.github.io/"
$cdnPrefix = "/_cdn/"   # 요청 경로가 /_cdn/ 로 시작하면 원격에서 가져와 캐시 후 제공
$cdnCacheRoot = Join-Path $webRoot "_cdn_cache"

function Get-CachedCdnFilePath([string]$cdnPath) {
  # cdnPath 예: "archives/0.9/pythons.js"
  $safeRel = $cdnPath -replace "/", "\"
  $safeRel = $safeRel.TrimStart("\")
  return Join-Path $cdnCacheRoot $safeRel
}

function Fetch-CdnBytes([string]$cdnPath) {
  $url = $remoteCdnBase.TrimEnd("/") + "/" + $cdnPath.TrimStart("/")
  try {
    $client = New-Object System.Net.WebClient
    # 사내 환경에서 TLS/프록시가 걸릴 수 있으니 기본 동작 사용
    return $client.DownloadData($url)
  } catch {
    return $null
  }
}

# HttpListener는 URL ACL(권한) 이슈가 있을 수 있어, TcpListener로 최소 HTTP 서버를 구현합니다.
# 또한 일부 환경에서 localhost가 IPv6(::1)로 해석될 수 있어, DualMode로 IPv4/IPv6 모두 받습니다.
$port = 8000
$listener = $null
while ($port -le 8010) {
  try {
    # IPv6Any + DualMode => ::1 / 127.0.0.1 둘 다 수신
    $listener = New-Object System.Net.Sockets.TcpListener ([System.Net.IPAddress]::IPv6Any, $port)
    $listener.Server.DualMode = $true
    $listener.Start()
    break
  }
  catch {
    try { if ($listener) { $listener.Stop() } } catch {}
    $listener = $null
    $port++
  }
}

if (-not $listener) {
  Write-Host "❌ 8000~8010 포트에서 로컬 서버를 시작하지 못했습니다. (이미 사용 중일 수 있음)" -ForegroundColor Red
  exit 1
}

$baseUrlLocalhost = "http://localhost:$port/"
$baseUrlIPv4 = "http://127.0.0.1:$port/"
Write-Host "✅ 로컬 웹 서버 시작" -ForegroundColor Green
Write-Host "브라우저에서 열기(권장): $baseUrlIPv4"
Write-Host "브라우저에서 열기(대안): $baseUrlLocalhost"
Write-Host "종료: 이 창에서 Ctrl+C"
Write-Host ""

try {
  while ($true) {
    $client = $listener.AcceptTcpClient()
    try {
      $stream = $client.GetStream()
      $reader = New-Object System.IO.StreamReader($stream, [Text.Encoding]::ASCII, $false, 1024, $true)

      $requestLine = $reader.ReadLine()
      if (-not $requestLine) { continue }

      # 헤더는 여기서는 버림(빈 줄까지 소비)
      while ($true) {
        $line = $reader.ReadLine()
        if ($line -eq $null -or $line -eq "") { break }
      }

      $parts = $requestLine.Split(" ")
      $method = $parts[0]
      $path = if ($parts.Length -ge 2) { $parts[1] } else { "/" }

      if ($method -ne "GET" -and $method -ne "HEAD") {
        $body = [Text.Encoding]::UTF8.GetBytes("405 Method Not Allowed")
        Write-HttpResponse $stream 405 "Method Not Allowed" "text/plain; charset=utf-8" $body
        continue
      }

      if ($path -eq "/" -or [string]::IsNullOrWhiteSpace($path)) {
        $path = "/index.html"
      }

      # querystring 제거
      if ($path.Contains("?")) { $path = $path.Split("?")[0] }

      # pygbag CDN 리소스를 same-origin으로 프록시: /_cdn/{원격경로}
      if ($path.StartsWith($cdnPrefix)) {
        $cdnPath = $path.Substring($cdnPrefix.Length)  # ex) "archives/0.9/pythons.js"
        $cdnPath = [Uri]::UnescapeDataString($cdnPath)

        $cachedPath = Get-CachedCdnFilePath $cdnPath
        $cachedDir = Split-Path -Parent $cachedPath
        if (-not (Test-Path $cachedDir)) { New-Item -ItemType Directory -Path $cachedDir -Force | Out-Null }

        if (-not (Test-Path $cachedPath)) {
          $bytes = Fetch-CdnBytes $cdnPath
          if ($bytes -eq $null) {
            $msg = "CDN 리소스를 내려받지 못했습니다: $remoteCdnBase$cdnPath`n사내망에서 외부 접속이 차단되었을 수 있습니다."
            Write-Host "❌ CDN 다운로드 실패: $remoteCdnBase$cdnPath" -ForegroundColor Red
            $body = [Text.Encoding]::UTF8.GetBytes($msg)
            Write-HttpResponse $stream 502 "Bad Gateway" "text/plain; charset=utf-8" $body
            continue
          }
          [IO.File]::WriteAllBytes($cachedPath, $bytes)
        }

        $bytes = [IO.File]::ReadAllBytes($cachedPath)
        $ct = Get-ContentType $cachedPath
        if ($method -eq "HEAD") {
          Write-HttpHeadersOnly $stream 200 "OK" $ct $bytes.Length
        } else {
          Write-HttpResponse $stream 200 "OK" $ct $bytes
        }
        Write-Host "$method $path -> 200 (cdn cached)" -ForegroundColor DarkGray
        continue
      }

      $relPath = $path.TrimStart("/") -replace "/", "\"
      $relPath = [Uri]::UnescapeDataString($relPath)

      # 경로 탈출 방지
      $targetPath = [IO.Path]::GetFullPath((Join-Path $webRoot $relPath))
      $rootFull = [IO.Path]::GetFullPath($webRoot)
      if (-not $targetPath.StartsWith($rootFull, [System.StringComparison]::OrdinalIgnoreCase)) {
        $body = [Text.Encoding]::UTF8.GetBytes("403 Forbidden")
        Write-HttpResponse $stream 403 "Forbidden" "text/plain; charset=utf-8" $body
        continue
      }

      if (-not (Test-Path $targetPath)) {
        $body = [Text.Encoding]::UTF8.GetBytes("404 Not Found")
        Write-HttpResponse $stream 404 "Not Found" "text/plain; charset=utf-8" $body
        Write-Host "$method $path -> 404" -ForegroundColor DarkGray
        continue
      }

      # index.html은 외부 CDN을 same-origin 프록시로 치환
      if ($targetPath.ToLowerInvariant().EndsWith("\index.html")) {
        $html = [IO.File]::ReadAllText($targetPath, [Text.Encoding]::UTF8)
        # 대표 CDN prefix들을 프록시로 교체
        $proxyBase = $baseUrlIPv4.TrimEnd("/") + $cdnPrefix
        $html = $html.Replace("https://pygame-web.github.io/", $proxyBase)
        $html = $html.Replace("https://pygame-web.github.io/archives/0.9/", $proxyBase + "archives/0.9/")
        $htmlBytes = [Text.Encoding]::UTF8.GetBytes($html)
        if ($method -eq "HEAD") {
          Write-HttpHeadersOnly $stream 200 "OK" "text/html; charset=utf-8" $htmlBytes.Length
        } else {
          Write-HttpResponse $stream 200 "OK" "text/html; charset=utf-8" $htmlBytes
        }
        Write-Host "$method $path -> 200 (index rewrite)" -ForegroundColor DarkGray
      } else {
        $bytes = [IO.File]::ReadAllBytes($targetPath)
        $ct = Get-ContentType $targetPath
        if ($method -eq "HEAD") {
          Write-HttpHeadersOnly $stream 200 "OK" $ct $bytes.Length
        } else {
          Write-HttpResponse $stream 200 "OK" $ct $bytes
        }
        Write-Host "$method $path -> 200" -ForegroundColor DarkGray
      }
    }
    finally {
      try { $client.Close() } catch {}
    }
  }
}
finally {
  try { $listener.Stop() } catch {}
}


