#!/bin/bash
# 走るウマ をビルドして .app を作る
set -e
DIR="$(cd "$(dirname "$0")" && pwd)"
APP="$DIR/走るウマ.app"

mkdir -p "$APP/Contents/MacOS"
cp "$DIR/Info.plist" "$APP/Contents/Info.plist"
clang -fobjc-arc -O2 "$DIR/main.m" -o "$APP/Contents/MacOS/RunUma" \
    -framework Cocoa -framework IOKit
codesign --force -s - "$APP"
echo "ビルド完了: $APP"
echo "起動: open '$APP'"
