function Get-ModifiedTimestamp{
<#
.SYNOPSIS
    Get the modified time of all files in a directory

.PARAMETER TargetDir
    The directory to check on

.PARAMETER Recursive
    If active, recursively work on subdirectories too

.PARAMETER Sort
    If active, the output will be sorted by timestamp in descending order

.PARAMETER PathOnly
    If active, will only output the path but not the timestamp
    Useful when making file indices together with -Sort

.PARAMETER NoConfirm
    If active, will not ask for confirmation on truncating output file
    Ignored if -Output is not set

.PARAMETER NoReturn
    If active, will not return output string in powershell

.PARAMETER FileTypes
    The filetype(s) to include in the checking. If omitted,
        will check on all file types

.PARAMETER Output
    File path of where the information should be written to.
        If omitted, will write to stdout
#>
    param(
        [Parameter(Mandatory)]
        [string]$TargetDir,
        [switch]$Recursive,
        [switch]$Sort,
        [switch]$PathOnly,
        [switch]$NoConfirm,
        [switch]$NoReturn,
        [string[]]$FileTypes = @(),
        [string]$Output = $null
    )

    # parameter validation and preparation
    if (-not (Test-Path -LiteralPath $TargetDir -PathType Container)) {
        throw "Path $TargetDir is not a valid directory"
    }
    $TargetDir = Resolve-Path -LiteralPath $TargetDir
    Write-Verbose "Working on $TargetDir"
    foreach ($ft in $FileTypes) {
        if ($ft -notmatch '^\.\w+$') {
            throw """$ft"" is not a valid dot-prefixed file extension"
        }
    }
    if ($FileTypes.Length -ne 0) {
        $FileTypes = "@(" + (($FileTypes | foreach {'"' + $_ + '"'}) -join ', ') + ")"
        Write-Verbose "Allowed file types: $FileTypes"
    } else {
        Write-Verbose "All file types allowed"
    }
    if (-not [string]::IsNullOrEmpty($Output)) {
        if (-not (Test-Path -LiteralPath $Output -PathType Leaf -IsValid)) {
            throw """$Output"" does not appear like a valid file path"
        } else {
            # (slightly) modified from https://stackoverflow.com/a/12605755
            # which comes from http://devhawk.net/blog/2010/1/22/fixing-powershells-busted-resolve-path-cmdlet
            $Output = Resolve-Path $Output -ErrorAction SilentlyContinue -ErrorVariable _frperror
            if (-not $Output) {
                $Output = $_frperror[0].TargetObject
            }
            Write-Verbose "Writing output to file $Output"
            if (Test-Path -LiteralPath $Output -PathType Leaf) {
                Write-Warning "$Output already exists. Fill will be overwritten"
                Clear-Content -LiteralPath $Output -Confirm:(-not $NoConfirm)
                if ((Get-Item $Output).Length -ne 0) {
                    throw "Content in ""$Output"" not cleared"
                }
            }
        }
    } else {
        Write-Verbose "Writing output to stdout"
    }

    $TargetDir = Resolve-Path -LiteralPath $TargetDir
    $RecurPara = "-Recurse:(`$$Recursive)"
    $FilterCmd = if ($FileTypes.Length -ne 0) {
        "| Where-Object Extension -in $FileTypes"
    } else {""}
    $QueryCmd = [ScriptBlock]::Create(@(
            "Get-ChildItem",
            "-LiteralPath $TargetDir",
            "-File",
            $RecurPara,
            $FilterCmd) -join " ")
    Write-Verbose "Query command: $QueryCmd"
    $QueryRes = $QueryCmd.Invoke()

    $OutFunc = if ([string]::IsNullOrEmpty($Output)) {
        {
            param([string]$InputString)
            Write-Host $InputString
        }
    } else {
        {
            param([string]$InputString)
            # Out-File -Encoding UTF8 -Append -LiteralPath $Output -InputObject $InputString
            [IO.File]::WriteAllText($Output, $InputString)
        }
    }
    $ProcessedFileCount = 0
    $OutputRes = $QueryRes.ForEach({
        $ProcessedFileCount += 1
        $RelPath = $_.FullName.replace((Resolve-Path '.').Path + '\', '')
        $Timestamp = ([DateTimeOffset]$_.LastWriteTimeUtc).ToUnixTimeSeconds()
        Write-Verbose "Processed file count: $ProcessedFileCount"
        return [PSCustomObject]@{timestamp=$Timestamp; path=$RelPath}
    })
    if ($Sort){
        $OutputRes = $OutputRes | Sort-Object -Property timestamp -Descending
    }
    # convert to string for output
    if ($PathOnly){
        $OutputRes = $OutputRes | ForEach-Object {$_.path}
    } else {
        $OutputRes = $OutputRes | ForEach-Object {"$($_.timestamp) $($_.path)"}
    }
    $OutFunc.Invoke($OutputRes -join "`n")
    if (-not $NoReturn){
        return $OutputRes
    }
}
