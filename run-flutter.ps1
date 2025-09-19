# HDFC Banking Flutter App Runner
# This script automatically detects the Flutter project and runs it

Write-Host "HDFC Banking Flutter App Runner" -ForegroundColor Green
Write-Host "===================================" -ForegroundColor Green

# Store the current directory to return to later
$originalDir = Get-Location

# Function to find Flutter project
function Find-FlutterProject {
    param([string]$searchPath)
    
    $pubspecFiles = Get-ChildItem -Path $searchPath -Name "pubspec.yaml" -Recurse -ErrorAction SilentlyContinue
    
    foreach ($pubspec in $pubspecFiles) {
        $fullPath = Join-Path $searchPath $pubspec
        $content = Get-Content $fullPath -ErrorAction SilentlyContinue
        
        if ($content -match "flutter:") {
            $projectDir = Split-Path $fullPath -Parent
            Write-Host "Found Flutter project: $projectDir" -ForegroundColor Green
            return $projectDir
        }
    }
    
    return $null
}

# Look for Flutter project
Write-Host "`nSearching for Flutter project..." -ForegroundColor Yellow

$flutterProject = Find-FlutterProject -searchPath (Get-Location)

if (-not $flutterProject) {
    Write-Host "No Flutter project found in the current directory tree!" -ForegroundColor Red
    Write-Host "Please make sure you're running this from the root of your project." -ForegroundColor Yellow
    exit 1
}

# Change to Flutter project directory
Write-Host "`nChanging to Flutter project directory..." -ForegroundColor Yellow
Set-Location $flutterProject

# Step 1: Fix JAVA_HOME and ANDROID_HOME environment variables
Write-Host "`nChecking and fixing environment variables..." -ForegroundColor Yellow

$correctJavaHome = "D:\Java(JDK , Projects)\JAVA RUNTIME\jdk-22"
if (Test-Path "$correctJavaHome\bin\java.exe") {
    $env:JAVA_HOME = $correctJavaHome
    Write-Host "JAVA_HOME set to: $env:JAVA_HOME" -ForegroundColor Green
} else {
    Write-Host "Warning: Java JDK not found at expected location" -ForegroundColor Yellow
}

$correctAndroidHome = "D:\Apps_coding\Code_Softwares"
if (Test-Path $correctAndroidHome) {
    $env:ANDROID_HOME = $correctAndroidHome
    Write-Host "ANDROID_HOME set to: $env:ANDROID_HOME" -ForegroundColor Green
} else {
    Write-Host "Warning: Android SDK not found at expected location" -ForegroundColor Yellow
}

# Step 2: Check if Flutter is installed
Write-Host "`nChecking Flutter installation..." -ForegroundColor Yellow

try {
    $flutterVersion = flutter --version 2>$null
    Write-Host "Flutter is installed" -ForegroundColor Green
} catch {
    Write-Host "Flutter is not installed or not in PATH!" -ForegroundColor Red
    Write-Host "Please install Flutter and add it to your PATH." -ForegroundColor Yellow
    Set-Location $originalDir
    exit 1
}

# Step 3: Get dependencies
Write-Host "`nGetting dependencies..." -ForegroundColor Yellow
flutter pub get

if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to get dependencies!" -ForegroundColor Red
    exit 1
}

# Step 4: Run flutter doctor
Write-Host "`nRunning Flutter doctor..." -ForegroundColor Yellow
flutter doctor

# Step 5: Check for connected devices
Write-Host "`nChecking for connected devices..." -ForegroundColor Yellow
$devices = flutter devices
Write-Host $devices

if ($devices -match "No devices detected") {
    Write-Host "No devices connected!" -ForegroundColor Yellow
    Write-Host "Please connect an Android device or start an emulator." -ForegroundColor Yellow
    
    $response = Read-Host "Do you want to continue anyway? (y/N)"
    if ($response -ne "y" -and $response -ne "Y") {
        Write-Host "Aborted by user." -ForegroundColor Yellow
        exit 0
    }
}

# Step 6: Generate code if needed (for json_serializable, etc.)
if (Test-Path "build_runner") {
    Write-Host "`nRunning code generation..." -ForegroundColor Yellow
    flutter packages pub run build_runner build --delete-conflicting-outputs
}

# Step 7: Run the app
Write-Host "`nStarting Flutter app..." -ForegroundColor Green
Write-Host "Available launch options:" -ForegroundColor Yellow
Write-Host "1. Chrome (Web) - Recommended for development" -ForegroundColor Gray
Write-Host "2. Android Device - Requires properly configured Android SDK" -ForegroundColor Gray

$choice = Read-Host "Choose launch option (1 for Chrome, 2 for Android, Enter for Chrome)"

if ($choice -eq "2") {
    Write-Host "Launching on Android device..." -ForegroundColor Cyan
    flutter run --android-skip-build-dependency-validation
} else {
    Write-Host "Launching on Chrome..." -ForegroundColor Cyan
    flutter run -d chrome
}

# Return to original directory
Set-Location $originalDir
Write-Host "`nReturned to root directory" -ForegroundColor Green