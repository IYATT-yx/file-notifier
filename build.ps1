$startTime = Get-Date

python -m venv venv
.\venv\Scripts\Activate.ps1
python.exe -m pip install --upgrade pip
pip install -r requirements.txt
pip install nuitka==2.8.9

python .\savebuildtime.py

nuitka --standalone --remove-output --windows-console-mode=disable `
--enable-plugin=tk-inter `
--windows-icon-from-ico=.\icon.ico --include-data-file=.\icon.ico=.\ `
--include-data-file=.\file-notifier.template=.\ `
--output-dir=dist --output-filename=file-notifier_win_amd64 `
.\file-notifier.py

$endTime = Get-Date
$elapsedTime = New-TimeSpan -Start $startTime -End $endTime
Write-Output "程序构建用时：$($elapsedTime.TotalSeconds) 秒"