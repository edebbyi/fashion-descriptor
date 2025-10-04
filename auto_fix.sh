#!/bin/bash
# Automated fix for Streamlit Cloud multi-page app issues
# This script adds shared initialization to all pages

echo "🔧 Fixing Streamlit Multi-Page App..."
echo ""

# Create shared_init.py
echo "📝 Creating ui/shared_init.py..."
cat > ui/shared_init.py << 'EOF'
# ui/shared_init.py
"""
Shared initialization for all Streamlit pages.
Import this at the top of every page file.
"""
import streamlit as st
import os
import sys
from pathlib import Path

# Add src to path (works from any page depth)
repo_root = Path(__file__).parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

def init_session_state():
    """Initialize all session state variables if they don't exist."""
    
    # API Keys
    if "gemini_api_key" not in st.session_state:
        st.session_state.gemini_api_key = os.getenv("GEMINI_API_KEY", "")
    
    if "openai_api_key" not in st.session_state:
        st.session_state.openai_api_key = os.getenv("OPENAI_API_KEY", "")
    
    # Analysis data
    if "analyzed_images" not in st.session_state:
        st.session_state.analyzed_images = []
    
    if "collection" not in st.session_state:
        st.session_state.collection = []
    
    if "engine" not in st.session_state:
        st.session_state.engine = None

def set_api_keys():
    """Set API keys as environment variables."""
    if st.session_state.gemini_api_key:
        os.environ["GEMINI_API_KEY"] = st.session_state.gemini_api_key
        os.environ["GOOGLE_API_KEY"] = st.session_state.gemini_api_key
    
    if st.session_state.openai_api_key:
        os.environ["OPENAI_API_KEY"] = st.session_state.openai_api_key

# Always initialize when this module is imported
init_session_state()
EOF

echo "✅ Created ui/shared_init.py"
echo ""

# Function to add import to a file
add_shared_init() {
    local file=$1
    local tmpfile="${file}.tmp"
    
    echo "📝 Updating $file..."
    
    # Create a temporary file with the new imports at the top
    {
        echo "import streamlit as st"
        echo "from pathlib import Path"
        echo "import sys"
        echo ""
        echo "# CRITICAL: Import shared initialization FIRST"
        
        # Different path depth for pages vs app.py
        if [[ $file == *"/pages/"* ]]; then
            echo "sys.path.insert(0, str(Path(__file__).parent.parent))"
        else
            echo "sys.path.insert(0, str(Path(__file__).parent.parent))"
        fi
        
        echo "from shared_init import init_session_state, set_api_keys"
        echo ""
        echo "# Initialize session state"
        echo "init_session_state()"
        echo ""
        
        # Add the rest of the file, skipping old imports
        grep -v "^import streamlit as st" "$file" | \
        grep -v "^from pathlib import Path" | \
        grep -v "^import sys" | \
        grep -v "^sys.path.insert"
    } > "$tmpfile"
    
    mv "$tmpfile" "$file"
    echo "✅ Updated $file"
}

# Update all page files
echo "📦 Updating page files..."
echo ""

for page in ui/pages/*.py; do
    if [ -f "$page" ]; then
        add_shared_init "$page"
    fi
done

echo ""
echo "✅ All pages updated!"
echo ""
echo "📝 Next steps:"
echo "  1. Review changes: git diff"
echo "  2. Test locally: streamlit run ui/app.py"
echo "  3. Commit: git add ui/"
echo "  4. Commit: git commit -m 'Fix: Add shared initialization for multi-page app'"
echo "  5. Push: git push"
echo ""
echo "🚀 After pushing, Streamlit Cloud will auto-redeploy and all pages should work!"