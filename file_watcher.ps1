# 감시할 폴더 경로 설정
$watchFolder = "C:\your\folder\path"  # 실제 폴더 경로로 변경하세요
$batchFile = "$watchFolder\sync.bat"   # 실행할 배치파일 경로

# FileSystemWatcher 객체 생성
$watcher = New-Object System.IO.FileSystemWatcher
$watcher.Path = $watchFolder
$watcher.Filter = "*.*"
$watcher.EnableRaisingEvents = $true
$watcher.IncludeSubdirectories = $true  # 하위 폴더도 감시하려면 $true

# 이벤트 핸들러 정의
$action = {
    $path = $Event.SourceEventArgs.FullPath
    $changeType = $Event.SourceEventArgs.ChangeType
    $timeStamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    
    # .git 폴더의 변화는 무시 (Git 내부 파일 변화로 인한 무한 루프 방지)
    if ($path -like "*\.git\*") {
        return
    }
    
    # 임시 파일이나 백업 파일 무시
    if ($path -match '\.(tmp|bak|~)

# 이벤트 등록
Register-ObjectEvent -InputObject $watcher -EventName "Created" -Action $action
Register-ObjectEvent -InputObject $watcher -EventName "Changed" -Action $action
Register-ObjectEvent -InputObject $watcher -EventName "Deleted" -Action $action
Register-ObjectEvent -InputObject $watcher -EventName "Renamed" -Action $action

Write-Host "파일 감시 시작: $watchFolder" -ForegroundColor Cyan
Write-Host "종료하려면 Ctrl+C를 누르세요..." -ForegroundColor Cyan

# 스크립트가 종료되지 않도록 대기
try {
    while ($true) {
        Start-Sleep 1
    }
} finally {
    # 정리 작업
    $watcher.Dispose()
    Write-Host "파일 감시 종료" -ForegroundColor Red
}) {
        return
    }
    
    Write-Host "[$timeStamp] $changeType: $path" -ForegroundColor Green
    
    # 배치파일이 존재하는지 확인 후 실행
    if (Test-Path $batchFile) {
        Write-Host "Git 자동 업데이트 실행 중..." -ForegroundColor Yellow
        
        # 관리자 권한으로 배치파일 실행
        Start-Process -FilePath "cmd.exe" -ArgumentList "/c", "`"$batchFile`"" -Verb RunAs -Wait
        
        Write-Host "Git 업데이트 완료!" -ForegroundColor Green
    } else {
        Write-Host "배치파일을 찾을 수 없습니다: $batchFile" -ForegroundColor Red
    }
}

# 이벤트 등록
Register-ObjectEvent -InputObject $watcher -EventName "Created" -Action $action
Register-ObjectEvent -InputObject $watcher -EventName "Changed" -Action $action
Register-ObjectEvent -InputObject $watcher -EventName "Deleted" -Action $action
Register-ObjectEvent -InputObject $watcher -EventName "Renamed" -Action $action

Write-Host "파일 감시 시작: $watchFolder" -ForegroundColor Cyan
Write-Host "종료하려면 Ctrl+C를 누르세요..." -ForegroundColor Cyan

# 스크립트가 종료되지 않도록 대기
try {
    while ($true) {
        Start-Sleep 1
    }
} finally {
    # 정리 작업
    $watcher.Dispose()
    Write-Host "파일 감시 종료" -ForegroundColor Red
}