#!/bin/bash
set -e

echo "🔧 Visual Descriptor - GitHub + Cloud Run Setup"
echo ""

# Check PROJECT_ID
if [ -z "$PROJECT_ID" ]; then
    echo "❌ Error: PROJECT_ID not set"
    echo "Usage: export PROJECT_ID=your-project-id && ./setup_github_deploy.sh"
    exit 1
fi

echo "📋 Project: $PROJECT_ID"
gcloud config set project $PROJECT_ID

# Enable APIs
echo ""
echo "✅ Step 1: Enabling APIs..."
gcloud services enable \
  cloudbuild.googleapis.com \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  secretmanager.googleapis.com

# Create Artifact Registry
echo ""
echo "✅ Step 2: Setting up Artifact Registry..."
if ! gcloud artifacts repositories describe visual-descriptor --location=us-central1 &>/dev/null; then
    gcloud artifacts repositories create visual-descriptor \
      --repository-format=docker \
      --location=us-central1 \
      --description="Visual Descriptor Docker images"
    echo "   Created repository"
else
    echo "   Repository already exists"
fi

# Setup Secrets
echo ""
echo "✅ Step 3: Setting up secrets..."

if ! gcloud secrets describe API_KEY &>/dev/null; then
    read -sp "Enter API_KEY (for authentication): " API_KEY
    echo ""
    echo -n "$API_KEY" | gcloud secrets create API_KEY --data-file=-
    echo "   Created API_KEY"
else
    echo "   API_KEY exists (update with: echo -n 'new_key' | gcloud secrets versions add API_KEY --data-file=-)"
fi

if ! gcloud secrets describe GEMINI_API_KEY &>/dev/null; then
    echo ""
    echo "Get your Gemini API key from: https://aistudio.google.com/app/apikey"
    read -sp "Enter GEMINI_API_KEY: " GEMINI_KEY
    echo ""
    echo -n "$GEMINI_KEY" | gcloud secrets create GEMINI_API_KEY --data-file=-
    echo "   Created GEMINI_API_KEY"
else
    echo "   GEMINI_API_KEY exists"
fi

# Grant permissions
echo ""
echo "✅ Step 4: Granting permissions..."
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")

# Cloud Run service account needs secret access
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member=serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com \
  --role=roles/secretmanager.secretAccessor \
  &>/dev/null

# Cloud Build service account needs Cloud Run admin
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member=serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com \
  --role=roles/run.admin \
  &>/dev/null

# Cloud Build needs to act as service accounts
gcloud iam service-accounts add-iam-policy-binding \
  ${PROJECT_NUMBER}-compute@developer.gserviceaccount.com \
  --member=serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com \
  --role=roles/iam.serviceAccountUser \
  &>/dev/null

echo "   Permissions granted"

echo ""
echo "🎉 Setup complete!"
echo ""
echo "Next steps:"
echo "1. Push your code to GitHub:"
echo "   git add ."
echo "   git commit -m 'Add Gemini integration'"
echo "   git push origin main"
echo ""
echo "2. Deploy manually:"
echo "   gcloud builds submit --config cloudbuild.yaml"
echo ""
echo "3. OR set up automatic deploys:"
echo "   Open: https://console.cloud.google.com/cloud-build/triggers?project=$PROJECT_ID"
echo "   Create a trigger connected to your GitHub repo"
echo ""
echo "4. Test your deployment:"
echo "   SERVICE_URL=\$(gcloud run services describe visual-descriptor --region=us-central1 --format='value(status.url)')"
echo "   curl \$SERVICE_URL/healthz"
