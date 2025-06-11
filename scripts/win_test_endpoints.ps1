# Define the file to upload
$filePath = "../tests/images/whale.jpg"

# List of endpoints
# $endpoints = @(
#     "http://localhost:29000/api/v1/predict",
#     "http://localhost:29000/api/v1/smart_predict",
#     "http://localhost:29000/api/v1/triton_predict"
# )

$endpoints = @(
    "http://localhost:30900/api/v1/predict",
    "http://localhost:30900/api/v1/smart_predict",
    "http://localhost:30900/api/v1/triton_predict"
)

# Loop through each endpoint and send the file
foreach ($endpoint in $endpoints) {
    Write-Host "Sending file to $endpoint ..."
    curl.exe -X POST `
        -H "Content-Type: multipart/form-data" `
        -F "file=@$filePath" `
        $endpoint

    Write-Host "`n"  # Add a blank line for readability
}

Write-Host "All endpoints tested."
