# Sample Job Specifications

This folder contains example job specifications for different environments:

## Folder Structure

- **`local/`** - Specs for local development with file system paths
- **`production/`** - Specs for AWS Lambda deployment with S3 URIs

## Key Differences

### Local Development (`local/`)

- Uses `./media/` file paths
- Includes `destination` field for local output
- Works with local file system

### Production/AWS Lambda (`production/`)

- Uses `s3://your-bucket-name/` URIs
- No `destination` field (Lambda handles S3 output automatically)
- Replace `your-bucket-name` with your actual S3 bucket name

## Usage

### For Local Testing

```bash
# Use local specs
python3 test_local.py samples/local/00_api_demo_video.spec.json
```

### For AWS Lambda

```bash
# Use production specs with your API
curl -X POST $API_URL/submit \
  -H "Content-Type: application/json" \
  -d @samples/production/00_api_demo_video.spec.json
```

## Setup for Production

1. Replace `your-bucket-name` in production specs with your actual bucket name
2. Ensure your S3 bucket has the required assets uploaded:
   ```bash
   aws s3 sync ./media/assets/ s3://your-bucket-name/assets/
   aws s3 sync ./media/inputs/ s3://your-bucket-name/inputs/
   ```

## Available Samples

- `00_api_demo_video.spec.json` - Basic API demonstration
- `01_short_video.spec.json` - Social media short with sound effects
- `02_explainer_video_french.spec.json` - French TTS explainer video
- `02_explainer_video_spanish.spec.json` - Spanish TTS explainer video
- `03_data_video.spec.json` - Complex data video with webhooks and audio ducking
