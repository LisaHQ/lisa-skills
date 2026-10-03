"""Scenario s5: Vietnamese internal backup scripts folder (create mode)."""
from fixture import w

ROOT = "s5-sao-luu-erp"


def build(base):
    r = base / ROOT
    w(r / "backup-db.ps1", r'''#Requires -Version 5.1
<#
.SYNOPSIS
  Sao lưu cơ sở dữ liệu ERP (SQL Server) hằng ngày, nén bằng 7-Zip và chép sang NAS.

.DESCRIPTION
  Đọc cấu hình từ config.json cùng thư mục. Tạo file .bak bằng sqlcmd
  (WITH COMPRESSION, CHECKSUM), nén thành .7z, chép sang thư mục NAS rồi xoá
  các bản sao lưu cũ hơn RetentionDays ngày ở cả máy chủ lẫn NAS.
  Ghi log theo ngày vào thư mục logs\. Nếu lỗi, gửi email cho nhóm IT.

.PARAMETER ConfigPath
  Đường dẫn file cấu hình. Mặc định: config.json cạnh script.

.PARAMETER SkipCopy
  Chỉ sao lưu và nén tại máy chủ, không chép sang NAS (dùng khi NAS bảo trì).

.EXAMPLE
  .\backup-db.ps1

.EXAMPLE
  .\backup-db.ps1 -SkipCopy
#>
param(
  [string]$ConfigPath = (Join-Path $PSScriptRoot 'config.json'),
  [switch]$SkipCopy
)

$ErrorActionPreference = 'Stop'
$cfg = Get-Content $ConfigPath -Raw -Encoding UTF8 | ConvertFrom-Json
$logDir = Join-Path $PSScriptRoot 'logs'
New-Item -ItemType Directory -Force $logDir | Out-Null
$log = Join-Path $logDir ((Get-Date -Format 'yyyy-MM-dd') + '.log')

function Write-Log([string]$msg) {
  $line = '[{0}] {1}' -f (Get-Date -Format 'HH:mm:ss'), $msg
  Add-Content -Path $log -Value $line -Encoding UTF8
}

try {
  Write-Log "Bắt đầu sao lưu $($cfg.Database)"
  $stamp = Get-Date -Format 'yyyyMMdd_HHmm'
  $bak = Join-Path $cfg.BackupDir "$($cfg.Database)_$stamp.bak"

  # Cần cài "SQL Server Command Line Utilities" (sqlcmd) trên máy chạy script.
  & sqlcmd -S $cfg.ServerInstance -U $cfg.SqlUser -P $cfg.SqlPassword -b `
    -Q "BACKUP DATABASE [$($cfg.Database)] TO DISK = N'$bak' WITH COMPRESSION, CHECKSUM, INIT"
  if ($LASTEXITCODE -ne 0) { throw "sqlcmd trả về mã lỗi $LASTEXITCODE" }

  # Nén bằng 7-Zip (đường dẫn trong SevenZipPath).
  & $cfg.SevenZipPath a -t7z -mx=5 "$bak.7z" $bak | Out-Null
  Remove-Item $bak
  Write-Log "Đã nén: $bak.7z ($([math]::Round((Get-Item "$bak.7z").Length / 1GB, 1)) GB)"

  if (-not $SkipCopy) {
    Copy-Item "$bak.7z" -Destination $cfg.NasPath
    Write-Log "Đã chép sang $($cfg.NasPath)"
  }

  # Xoá bản cũ hơn RetentionDays ngày (máy chủ và NAS).
  $limit = (Get-Date).AddDays(-[int]$cfg.RetentionDays)
  foreach ($dir in @($cfg.BackupDir, $cfg.NasPath)) {
    Get-ChildItem $dir -Filter "$($cfg.Database)_*.7z" |
      Where-Object LastWriteTime -lt $limit |
      Remove-Item
  }
  Write-Log 'Hoàn tất.'
}
catch {
  Write-Log "LỖI: $_"
  Send-MailMessage -SmtpServer $cfg.Smtp.Server -From $cfg.Smtp.From -To $cfg.Smtp.To `
    -Subject "[ERP Backup] Lỗi sao lưu $($cfg.Database)" -Body "$_" -Encoding UTF8
  exit 1
}
''')
    w(r / "restore-db.ps1", r'''#Requires -Version 5.1
<#
.SYNOPSIS
  Khôi phục cơ sở dữ liệu ERP từ một file .7z do backup-db.ps1 tạo ra.

.DESCRIPTION
  Giải nén file .7z vào BackupDir rồi RESTORE sang database đích.
  Mặc định khôi phục sang database MỚI tên <Database>_KhoiPhuc để kiểm tra,
  không đụng tới database đang chạy. Muốn ghi đè database đang tồn tại thì
  phải chỉ rõ -TargetDatabase và thêm -Force (dùng WITH REPLACE).

.PARAMETER BackupFile
  Đường dẫn file .7z cần khôi phục (bắt buộc).

.PARAMETER TargetDatabase
  Tên database đích. Mặc định: <Database>_KhoiPhuc.

.PARAMETER Force
  Cho phép ghi đè database đích nếu đã tồn tại.

.EXAMPLE
  .\restore-db.ps1 -BackupFile '\\nas01\backup\erp\ERP_Production_20240930_2330.bak.7z'

.EXAMPLE
  .\restore-db.ps1 -BackupFile D:\Backup\ERP\ERP_Production_20240930_2330.bak.7z -TargetDatabase ERP_Production -Force
#>
param(
  [Parameter(Mandatory)] [string]$BackupFile,
  [string]$TargetDatabase,
  [switch]$Force,
  [string]$ConfigPath = (Join-Path $PSScriptRoot 'config.json')
)

$ErrorActionPreference = 'Stop'
$cfg = Get-Content $ConfigPath -Raw -Encoding UTF8 | ConvertFrom-Json
if (-not $TargetDatabase) { $TargetDatabase = "$($cfg.Database)_KhoiPhuc" }

& $cfg.SevenZipPath e -y "-o$($cfg.BackupDir)" $BackupFile | Out-Null
$bak = Join-Path $cfg.BackupDir ([IO.Path]::GetFileNameWithoutExtension($BackupFile))

$replace = if ($Force) { ', REPLACE' } else { '' }
& sqlcmd -S $cfg.ServerInstance -U $cfg.SqlUser -P $cfg.SqlPassword -b `
  -Q "RESTORE DATABASE [$TargetDatabase] FROM DISK = N'$bak' WITH CHECKSUM, RECOVERY$replace"
if ($LASTEXITCODE -ne 0) { throw "Khôi phục thất bại (sqlcmd mã $LASTEXITCODE)" }
Remove-Item $bak
Write-Host "Đã khôi phục sang database $TargetDatabase"
''')
    w(r / "kiem-tra.ps1", r'''#Requires -Version 5.1
<#
.SYNOPSIS
  Kiểm tra bản sao lưu mới nhất trên NAS: phải có file .7z mới hơn 26 giờ và
  vượt qua kiểm tra toàn vẹn "7z t". Gửi email nếu không đạt.
#>
param([string]$ConfigPath = (Join-Path $PSScriptRoot 'config.json'))

$ErrorActionPreference = 'Stop'
$cfg = Get-Content $ConfigPath -Raw -Encoding UTF8 | ConvertFrom-Json
$latest = Get-ChildItem $cfg.NasPath -Filter "$($cfg.Database)_*.7z" |
  Sort-Object LastWriteTime -Descending | Select-Object -First 1

$problem = $null
if (-not $latest) { $problem = 'Không tìm thấy bản sao lưu nào trên NAS.' }
elseif ($latest.LastWriteTime -lt (Get-Date).AddHours(-26)) { $problem = "Bản mới nhất quá cũ: $($latest.Name)" }
else {
  & $cfg.SevenZipPath t $latest.FullName | Out-Null
  if ($LASTEXITCODE -ne 0) { $problem = "File hỏng: $($latest.Name)" }
}

if ($problem) {
  Send-MailMessage -SmtpServer $cfg.Smtp.Server -From $cfg.Smtp.From -To $cfg.Smtp.To `
    -Subject '[ERP Backup] Kiểm tra không đạt' -Body $problem -Encoding UTF8
  exit 1
}
Write-Host "OK: $($latest.Name)"
''')
    w(r / "config.json", r'''{
  "ServerInstance": "ERP-SQL01\\ERP",
  "Database": "ERP_Production",
  "SqlUser": "backup_user",
  "SqlPassword": "Bk@2024!erp#Prod",
  "BackupDir": "D:\\Backup\\ERP",
  "NasPath": "\\\\nas01\\backup\\erp",
  "RetentionDays": 14,
  "SevenZipPath": "C:\\Program Files\\7-Zip\\7z.exe",
  "Smtp": {
    "Server": "mail.example.invalid",
    "From": "erp-backup@example.invalid",
    "To": "it-team@example.invalid"
  }
}
''')
    w(r / "lich-chay.md", '''\
# Lịch chạy (Task Scheduler trên ERP-SQL01)

| Tác vụ | Script | Giờ chạy | Tài khoản |
| --- | --- | --- | --- |
| ERP Backup | backup-db.ps1 | 23:30 hằng ngày | svc_backup |
| ERP Backup Verify | kiem-tra.ps1 | 06:00 hằng ngày | svc_backup |

Lệnh trong tác vụ: `powershell.exe -NoProfile -ExecutionPolicy Bypass -File D:\\Scripts\\sao-luu-erp\\backup-db.ps1`
''')
    w(r / "logs/2024-09-30.log", '''\
[23:30:02] Bắt đầu sao lưu ERP_Production
[23:41:15] Đã nén: D:\\Backup\\ERP\\ERP_Production_20240930_2330.bak.7z (3.2 GB)
[23:44:51] Đã chép sang \\\\nas01\\backup\\erp
[23:44:53] Hoàn tất.
''')
