#!/bin/bash
# Temporarily disable gitignore for development

echo "⚠️  WARNING: This will temporarily disable .gitignore"
echo "Use this only for development and restore it after!"
echo ""

# Backup current .gitignore
cp .gitignore .gitignore.backup

# Create minimal .gitignore
cat > .gitignore.minimal << 'EOF'
# Minimal gitignore - TEMPORARY
.env
*.pyc
__pycache__/
.venv/
EOF

echo "Choose an option:"
echo "1) Use minimal .gitignore (keeps only critical exclusions)"
echo "2) Completely disable .gitignore (tracks everything)"
echo "3) Restore original .gitignore"
read -p "Enter choice (1-3): " choice

case $choice in
    1)
        cp .gitignore.minimal .gitignore
        echo "✅ Switched to minimal .gitignore"
        echo "Critical files (.env, .venv) are still protected"
        ;;
    2)
        mv .gitignore .gitignore.disabled
        echo "✅ .gitignore completely disabled"
        echo "⚠️  WARNING: All files will be tracked!"
        ;;
    3)
        if [ -f .gitignore.backup ]; then
            cp .gitignore.backup .gitignore
            echo "✅ Original .gitignore restored"
        else
            echo "❌ No backup found"
        fi
        ;;
    *)
        echo "Invalid choice"
        ;;
esac

echo ""
echo "Current git status:"
git status --short