[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$projectPath = Join-Path $PSScriptRoot '..\src\ForexIntelligence.Api'

function Read-DefaultValue {
    param(
        [Parameter(Mandatory)] [string] $Label,
        [Parameter(Mandatory)] [string] $Default
    )

    $value = Read-Host "$Label [$Default]"
    if ([string]::IsNullOrWhiteSpace($value)) { return $Default }
    return $value
}

function ConvertTo-PlainText {
    param([Parameter(Mandatory)] [System.Security.SecureString] $SecureValue)

    $pointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($SecureValue)
    try {
        return [Runtime.InteropServices.Marshal]::PtrToStringBSTR($pointer)
    }
    finally {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($pointer)
    }
}

function New-RandomSecret {
    $bytes = New-Object byte[] 48
    $generator = [System.Security.Cryptography.RandomNumberGenerator]::Create()
    try {
        $generator.GetBytes($bytes)
        return [Convert]::ToBase64String($bytes)
    }
    finally {
        $generator.Dispose()
        [Array]::Clear($bytes, 0, $bytes.Length)
    }
}

function Set-ProjectSecret {
    param(
        [Parameter(Mandatory)] [string] $Key,
        [Parameter(Mandatory)] [string] $Value
    )

    & dotnet user-secrets set $Key $Value --project $projectPath | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "Gagal menyimpan user secret '$Key'." }
}

Write-Host 'Forex Intelligence development setup'
Write-Host 'Nilai rahasia disimpan di .NET User Secrets dan tidak ditulis ke repository.'

$databaseHost = Read-DefaultValue -Label 'PostgreSQL host' -Default '127.0.0.1'
$databasePort = Read-DefaultValue -Label 'PostgreSQL port' -Default '5432'
$databaseName = Read-DefaultValue -Label 'Database name' -Default 'forex_intelligence'
$databaseUser = Read-DefaultValue -Label 'Database user' -Default 'forex_app'
$databasePasswordSecure = Read-Host 'Database password' -AsSecureString
$databasePassword = ConvertTo-PlainText $databasePasswordSecure
if ([string]::IsNullOrWhiteSpace($databasePassword)) { throw 'Database password tidak boleh kosong.' }
$escapedDatabasePassword = $databasePassword.Replace('"', '""')
$connectionString = "Host=$databaseHost;Port=$databasePort;Database=$databaseName;Username=$databaseUser;Password=`"$escapedDatabasePassword`""

$bootstrapUsername = Read-DefaultValue -Label 'Bootstrap admin username' -Default 'admin'
$bootstrapPasswordSecure = Read-Host 'Bootstrap admin password' -AsSecureString
$bootstrapPassword = ConvertTo-PlainText $bootstrapPasswordSecure
if ([string]::IsNullOrWhiteSpace($bootstrapPassword)) { throw 'Bootstrap password tidak boleh kosong.' }

$hashOutput = $bootstrapPassword | & dotnet run --project $projectPath -- --hash-password
if ($LASTEXITCODE -ne 0) { throw 'Gagal membuat bootstrap password hash.' }
$passwordHash = $hashOutput | Where-Object { $_ -match '^pbkdf2-sha256\$' } | Select-Object -Last 1
if ([string]::IsNullOrWhiteSpace($passwordHash)) { throw 'Output bootstrap password hash tidak ditemukan.' }

$jwtSigningKey = New-RandomSecret
$bridgeApiKey = New-RandomSecret

Set-ProjectSecret 'ConnectionStrings:PostgreSql' $connectionString
Set-ProjectSecret 'Jwt:SigningKey' $jwtSigningKey
Set-ProjectSecret 'BridgeAuthentication:ApiKey' $bridgeApiKey
Set-ProjectSecret 'BootstrapUser:Username' $bootstrapUsername
Set-ProjectSecret 'BootstrapUser:PasswordHash' $passwordHash
Set-ProjectSecret 'BootstrapUser:Role' 'ADMIN'

$databasePassword = $null
$bootstrapPassword = $null
$connectionString = $null
$jwtSigningKey = $null

Write-Host ''
Write-Host 'Development secrets berhasil dikonfigurasi.' -ForegroundColor Green
Write-Host 'Simpan bridge API key berikut di password manager, lalu gunakan sebagai'
Write-Host 'MT5_BRIDGE_BACKEND_API_KEY pada laptop server:'
Write-Host $bridgeApiKey -ForegroundColor Yellow
Write-Host ''
Write-Host 'Jangan kirim key tersebut ke chat dan jangan commit ke Git.'
