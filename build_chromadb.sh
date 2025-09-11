#!/bin/bash
# Build script for ChromaDB on Render

echo "🔧 Starting ChromaDB build process..."

# Use python3 for local testing, python for Render
PYTHON_CMD="python3"
if command -v python &> /dev/null; then
    PYTHON_CMD="python"
fi

# Upgrade pip
echo "📦 Upgrading pip..."
$PYTHON_CMD -m pip install --upgrade pip

# Install ChromaDB first (let it pull its own dependencies)
echo "📦 Installing ChromaDB..."
$PYTHON_CMD -m pip install chromadb==0.4.18

# Install other dependencies
echo "📦 Installing other dependencies..."
$PYTHON_CMD -m pip install -r backend/requirements-prod-minimal.txt

# Create ChromaDB directory (use local path for testing)
echo "📁 Creating ChromaDB directory..."
if [ -d "/opt/render" ]; then
    CHROMA_PATH="/opt/render/project/src/chroma_db"
else
    CHROMA_PATH="./test_chroma_build"
fi
mkdir -p $CHROMA_PATH
rm -rf $CHROMA_PATH/*

# Test ChromaDB import
echo "🧪 Testing ChromaDB import..."
$PYTHON_CMD -c "
try:
    import chromadb
    print('✅ ChromaDB imported successfully')
    print(f'   Version: {chromadb.__version__}')
    
    from chromadb.config import Settings
    print('✅ Settings imported successfully')
    
    client = chromadb.PersistentClient()
    print('✅ ChromaDB client created successfully')
    
    # Test with Settings
    settings = Settings(is_persistent=True, persist_directory='$CHROMA_PATH')
    persistent_client = chromadb.PersistentClient(settings=settings)
    print('✅ ChromaDB persistent client created successfully')
    
    print('🎉 ChromaDB is working correctly!')
    
except ImportError as e:
    print(f'❌ ChromaDB import failed: {e}')
    exit(1)
except Exception as e:
    print(f'❌ ChromaDB test failed: {e}')
    exit(1)
"

if [ $? -eq 0 ]; then
    echo "✅ Build completed successfully!"
else
    echo "❌ Build failed!"
    exit 1
fi
