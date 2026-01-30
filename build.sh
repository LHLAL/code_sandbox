#!/bin/bash

# 默认镜像名称
IMAGE_NAME="manus-sandbox"

echo "Select target architecture:"
echo "1) x86_64 (Standard Linux)"
echo "2) ARM64 (Kylin V10 / Apple Silicon)"
echo "3) Multi-arch (using Buildx)"
read -p "Enter choice [1-3]: " choice

case $choice in
    1)
        echo "Building for x86_64..."
        docker build -f Dockerfile.x86 -t ${IMAGE_NAME}:x86_64 .
        ;;
    2)
        echo "Building for ARM64 (Kylin V10)..."
        docker build -f Dockerfile.arm64 -t ${IMAGE_NAME}:arm64 .
        ;;
    3)
        echo "Building multi-arch image using Buildx..."
        # 确保已创建 buildx 实例
        docker buildx create --use --name mybuilder || true
        docker buildx build --platform linux/amd64,linux/arm64 -t ${IMAGE_NAME}:latest --push .
        ;;
    *)
        echo "Invalid choice"
        exit 1
        ;;
esac

echo "Build complete."
