param(
    [Parameter(Mandatory=$true)][string]$ImagePath
)

$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Runtime.WindowsRuntime
[void][Windows.Media.Ocr.OcrEngine, Windows.Foundation, ContentType = WindowsRuntime]
[void][Windows.Graphics.Imaging.BitmapDecoder, Windows.Graphics, ContentType = WindowsRuntime]
[void][Windows.Storage.StorageFile, Windows.Storage, ContentType = WindowsRuntime]
[void][Windows.Globalization.Language, Windows.Globalization, ContentType = WindowsRuntime]

function AwaitAction($asyncOp, $targetType) {
    $asTaskMethods = [System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object { 
        $_.Name -eq 'AsTask' -and $_.IsGenericMethodDefinition 
    }
    $genMethod = $asTaskMethods[0].MakeGenericMethod($targetType)
    $task = $genMethod.Invoke($null, @($asyncOp))
    $task.Wait()
    return $task.Result
}

try {
    $fullPath = [System.IO.Path]::GetFullPath($ImagePath)
    $fileOp = [Windows.Storage.StorageFile]::GetFileFromPathAsync($fullPath)
    $file = AwaitAction $fileOp ([Windows.Storage.StorageFile])

    $streamOp = $file.OpenAsync([Windows.Storage.FileAccessMode]::Read)
    $stream = AwaitAction $streamOp ([Windows.Storage.Streams.IRandomAccessStream])

    $decoderOp = [Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($stream)
    $decoder = AwaitAction $decoderOp ([Windows.Graphics.Imaging.BitmapDecoder])

    $bitmapOp = $decoder.GetSoftwareBitmapAsync()
    $bitmap = AwaitAction $bitmapOp ([Windows.Graphics.Imaging.SoftwareBitmap])

    $engine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromUserProfileLanguages()
    if (-not $engine) {
        $engine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromLanguage([Windows.Globalization.Language]::new("en-US"))
    }

    $ocrOp = $engine.RecognizeAsync($bitmap)
    $result = AwaitAction $ocrOp ([Windows.Media.Ocr.OcrResult])

    $lines = @()
    if ($result.Lines) {
        foreach ($line in $result.Lines) {
            $lines += $line.Text
        }
    }

    $output = @{
        Success = $true
        FullText = $result.Text
        Lines = $lines
        LineCount = $lines.Count
        TextAngle = $result.TextAngle
    }
    $output | ConvertTo-Json -Compress
} catch {
    $errOutput = @{
        Success = $false
        Error = $_.Exception.Message
        FullText = ""
        Lines = @()
    }
    $errOutput | ConvertTo-Json -Compress
}
