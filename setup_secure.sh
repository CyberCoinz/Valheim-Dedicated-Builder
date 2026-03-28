#!/bin/bash
# Secure setup script for Valheim Builder
# This helps set up local configuration without exposing credentials

echo "🔒 Valheim Builder - Secure Setup"
echo "=================================="
echo ""

# Check if local config exists
if [ -f "config/local.yml" ]; then
    echo "⚠️  Local config already exists at config/local.yml"
    echo "   Edit it manually or delete it to recreate."
    exit 1
fi

echo "📋 Copying template to config/local.yml..."
cp config/local.yml.example config/local.yml

echo ""
echo "✅ Template copied! Now edit config/local.yml with your credentials:"
echo "   - SSH keys and passwords"
echo "   - ESXi connection details"
echo "   - Known host configurations"
echo ""
echo "⚠️  IMPORTANT: Never commit config/local.yml to git!"
echo "   It contains sensitive information."
echo ""
echo "Edit with: nano config/local.yml"
echo "Or:       vim config/local.yml"