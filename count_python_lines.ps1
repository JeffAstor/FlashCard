# PowerShell script to count total lines in all .py files in the FlashCard project
# Created: October 15, 2025

Write-Host "Counting lines in Python files..." -ForegroundColor Green
Write-Host "=================================" -ForegroundColor Green

# Get all .py files in the current directory and subdirectories, excluding virtual environment and cache folders
$pythonFiles = Get-ChildItem -Path "." -Filter "*.py" -Recurse | Where-Object {
    $_.FullName -notmatch "\\flash_cards\\" -and 
    $_.FullName -notmatch "\\__pycache__\\" -and
    $_.FullName -notmatch "\\\.git\\"
}

# Initialize counters
$totalLines = 0
$totalFiles = 0
$fileDetails = @()

# Process each Python file
foreach ($file in $pythonFiles) {
    try {
        # Read the file and count lines
        $content = Get-Content -Path $file.FullName -ErrorAction Stop
        $lineCount = $content.Count
        
        # Handle empty files (Get-Content returns $null for empty files)
        if ($null -eq $lineCount) {
            $lineCount = 0
        }
        
        # Add to totals
        $totalLines += $lineCount
        $totalFiles++
        
        # Store file details for detailed report
        $fileDetails += [PSCustomObject]@{
            File = $file.FullName.Replace((Get-Location).Path + "\", "")
            Lines = $lineCount
            Size = [math]::Round($file.Length / 1KB, 2)
        }
        
        Write-Host "  $($file.Name): $lineCount lines" -ForegroundColor Cyan
    }
    catch {
        Write-Warning "Could not read file: $($file.FullName) - $($_.Exception.Message)"
    }
}

Write-Host "`n=================================" -ForegroundColor Green
Write-Host "SUMMARY:" -ForegroundColor Yellow
Write-Host "Total Python files: $totalFiles" -ForegroundColor White
Write-Host "Total lines of code: $totalLines" -ForegroundColor White

# Display top 10 largest files by line count
Write-Host "`nTop 10 largest Python files by line count:" -ForegroundColor Yellow
$fileDetails | Sort-Object Lines -Descending | Select-Object -First 10 | Format-Table -AutoSize

# Optional: Save detailed report to file
$reportPath = "python_line_count_report.txt"
$report = @"
FlashCard Project - Python Files Line Count Report
Generated: $(Get-Date)
================================================

SUMMARY:
- Total Python files: $totalFiles
- Total lines of code: $totalLines

DETAILED BREAKDOWN:
$($fileDetails | Sort-Object Lines -Descending | ForEach-Object { "  $($_.File): $($_.Lines) lines ($($_.Size) KB)" } | Out-String)
"@

$report | Out-File -FilePath $reportPath -Encoding UTF8
Write-Host "`nDetailed report saved to: $reportPath" -ForegroundColor Green