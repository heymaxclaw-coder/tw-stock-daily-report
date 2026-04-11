# Alpha Daily Scanner - Cron 設定

## 自動執行時間
每天 20:00 台灣時間 (12:00 UTC)

## 設定指令
```bash
# 編輯 crontab
crontab -e

# 加入這行：
0 12 * * * /home/node/.openclaw/workspace/projects/tw-stock-daily-report/scripts/alpha/daily_report.sh >> /tmp/alpha_scanner.log 2>&1
```

## 手動執行
```bash
cd /home/node/.openclaw/workspace/projects/tw-stock-daily-report
python3 scripts/alpha/daily_scanner.py
```

## 查看日誌
```bash
cat /tmp/alpha_scanner.log
```
