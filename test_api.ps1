# HDFC API Test Script
# This script tests all API endpoints to ensure they work correctly

Write-Host "🧪 HDFC Card Limit System API Test" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan

# Check if server is running
Write-Host "`n1. Testing Server Health..." -ForegroundColor Yellow

try {
    $healthResponse = Invoke-WebRequest -Uri "http://localhost:8000/api/health/" -Method GET -UseBasicParsing
    $healthData = $healthResponse.Content | ConvertFrom-Json
    Write-Host "✅ Server is healthy!" -ForegroundColor Green
    Write-Host "   Status: $($healthData.status)" -ForegroundColor Gray
    Write-Host "   Message: $($healthData.message)" -ForegroundColor Gray
}
catch {
    Write-Host "❌ Server health check failed!" -ForegroundColor Red
    Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "   Please start the server first: py Backend\card_limit_system\simple_server.py" -ForegroundColor Yellow
    exit 1
}

# Test customer data submission
Write-Host "`n2. Testing Customer Data Submission..." -ForegroundColor Yellow

$customerData = @{
    name = "John Doe"
    email = "john.doe@email.com"
    phone = "+91-9876543210"
    customer_id = "CUST001"
} | ConvertTo-Json

try {
    $customerResponse = Invoke-WebRequest -Uri "http://localhost:8000/api/customers/" -Method POST -Body $customerData -ContentType "application/json" -UseBasicParsing
    $customerResult = $customerResponse.Content | ConvertFrom-Json
    Write-Host "✅ Customer data submitted successfully!" -ForegroundColor Green
    Write-Host "   Customer ID: $($customerResult.data.id)" -ForegroundColor Gray
    Write-Host "   Status: $($customerResult.status)" -ForegroundColor Gray
}
catch {
    Write-Host "❌ Customer submission failed!" -ForegroundColor Red
    Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Red
}

# Test limit request submission
Write-Host "`n3. Testing Limit Request Submission..." -ForegroundColor Yellow

$limitRequestData = @{
    customer_id = "CUST001"
    customer_name = "John Doe"
    email = "john.doe@email.com"
    phone = "+91-9876543210"
    request_type = "limit_increase"
    current_limit = 50000
    requested_limit = 100000
    reason = "Salary increase and improved credit score"
    income_proof = "salary_slip_2025.pdf"
} | ConvertTo-Json

try {
    $requestResponse = Invoke-WebRequest -Uri "http://localhost:8000/api/limit-requests/" -Method POST -Body $limitRequestData -ContentType "application/json" -UseBasicParsing
    $requestResult = $requestResponse.Content | ConvertFrom-Json
    Write-Host "✅ Limit request submitted successfully!" -ForegroundColor Green
    Write-Host "   Request ID: $($requestResult.data.id)" -ForegroundColor Gray
    Write-Host "   Status: $($requestResult.data.status)" -ForegroundColor Gray
    $requestId = $requestResult.data.id
}
catch {
    Write-Host "❌ Limit request submission failed!" -ForegroundColor Red
    Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Red
    $requestId = "dummy-id"
}

# Test getting recent requests
Write-Host "`n4. Testing Recent Requests Retrieval..." -ForegroundColor Yellow

try {
    $recentResponse = Invoke-WebRequest -Uri "http://localhost:8000/api/limit-requests/recent/" -Method GET -UseBasicParsing
    $recentResult = $recentResponse.Content | ConvertFrom-Json
    Write-Host "✅ Recent requests retrieved successfully!" -ForegroundColor Green
    Write-Host "   Total requests: $($recentResult.count)" -ForegroundColor Gray
    
    if ($recentResult.count -gt 0) {
        Write-Host "   Latest request:" -ForegroundColor Gray
        $latest = $recentResult.data[-1]
        Write-Host "     ID: $($latest.id)" -ForegroundColor Gray
        Write-Host "     Customer: $($latest.customer_name)" -ForegroundColor Gray
        Write-Host "     Type: $($latest.request_type)" -ForegroundColor Gray
        Write-Host "     Status: $($latest.status)" -ForegroundColor Gray
    }
}
catch {
    Write-Host "❌ Recent requests retrieval failed!" -ForegroundColor Red
    Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Red
}

# Test request status check
Write-Host "`n5. Testing Request Status Check..." -ForegroundColor Yellow

try {
    $statusResponse = Invoke-WebRequest -Uri "http://localhost:8000/api/limit-requests/$requestId/status/" -Method GET -UseBasicParsing
    $statusResult = $statusResponse.Content | ConvertFrom-Json
    Write-Host "✅ Request status retrieved successfully!" -ForegroundColor Green
    Write-Host "   Request ID: $($statusResult.data.id)" -ForegroundColor Gray
    Write-Host "   Status: $($statusResult.data.status)" -ForegroundColor Gray
    Write-Host "   Message: $($statusResult.data.message)" -ForegroundColor Gray
}
catch {
    Write-Host "❌ Request status check failed!" -ForegroundColor Red
    Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Red
}

# Check generated data files
Write-Host "`n6. Checking Generated Data Files..." -ForegroundColor Yellow

$dataDir = "Backend\card_limit_system\api_data"
if (Test-Path $dataDir) {
    Write-Host "✅ Data directory exists!" -ForegroundColor Green
    
    $files = Get-ChildItem $dataDir -Filter "*.json"
    foreach ($file in $files) {
        $content = Get-Content $file.FullName | ConvertFrom-Json
        Write-Host "   📄 $($file.Name): $($content.Count) records" -ForegroundColor Gray
    }
    
    # Check for Oracle insert statements
    $sqlFile = Join-Path $dataDir "oracle_inserts.sql"
    if (Test-Path $sqlFile) {
        $sqlContent = Get-Content $sqlFile
        Write-Host "   📄 oracle_inserts.sql: $($sqlContent.Count) lines" -ForegroundColor Gray
    }
} else {
    Write-Host "❌ Data directory not found!" -ForegroundColor Red
}

Write-Host "`n🎉 API Test Complete!" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "Next Steps:" -ForegroundColor White
Write-Host "1. Execute oracle_setup.sql in Oracle SQL Developer" -ForegroundColor Yellow
Write-Host "2. Configure Flutter app to use http://localhost:8000/api" -ForegroundColor Yellow
Write-Host "3. Run oracle_live_monitoring.sql to see live data" -ForegroundColor Yellow
Write-Host "4. Start the live demo! 🚀" -ForegroundColor Green