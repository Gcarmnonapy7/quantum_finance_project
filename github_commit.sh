#!/bin/bash
set -e

# Default commit message if none provided
COMMIT_MSG="${1:-Update project files and configuration}"

echo "Staging files..."
git add .

echo "Committing: '$COMMIT_MSG'..."
git commit -m "$COMMIT_MSG"

echo "Pushing to GitHub (origin/main)..."
git push origin main

echo "Successfully pushed to GitHub!"
set -e

# Default commit message if none provided
COMMIT_MSG="${1:-Update project files and configuration}"

echo "Staging files..."
git add .

echo "Committing: '$COMMIT_MSG'..."
git commit -m "$COMMIT_MSG"

echo "Pushing to GitHub (origin/main)..."
git push origin main

echo "Successfully pushed to GitHub!"
