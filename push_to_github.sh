#!/bin/bash
# push_to_github.sh - 推送 Agent Workflow Template 到 GitHub

echo "🚀 Agent Workflow Template - GitHub 推送指南"
echo "=========================================="
echo ""

# 顏色定義
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}📋 準備工作：${NC}"
echo "1. 前往 GitHub 建立新的 Repository"
echo "   https://github.com/new"
echo ""
echo "   Repository name: agent-workflow-template"
echo "   Description: AI Agent 多角色協作開發工作流程系統"
echo "   ✅ Public (推薦) - 讓其他人也能用此 Template"
echo "   ❌ 不要勾選 'Initialize with README' (我們已有檔案)"
echo ""

read -p "已在 GitHub 建立 Repository 了嗎？(y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "請先建立 Repository 再執行此腳本"
    exit 1
fi

echo ""
echo -e "${BLUE}🔗 請輸入你的 GitHub 資訊：${NC}"
read -p "GitHub 使用者名稱: " GITHUB_USER
read -p "Repository 名稱 (預設: agent-workflow-template): " REPO_NAME
REPO_NAME=${REPO_NAME:-agent-workflow-template}

echo ""
echo -e "${YELLOW}📤 準備推送到：${NC}"
echo "   https://github.com/$GITHUB_USER/$REPO_NAME"
echo ""

read -p "確認推送？(y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "取消推送"
    exit 1
fi

# 切換到專案目錄
cd /tmp/agent-workflow-template

# 設定 remote
echo -e "${BLUE}[1/3] 設定 remote...${NC}"
git remote add origin "https://github.com/$GITHUB_USER/$REPO_NAME.git"

# 推送
echo -e "${BLUE}[2/3] 推送到 GitHub...${NC}"
git push -u origin main

# 完成
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✅ 推送完成！${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${YELLOW}📝 下一步：確認 downstream 交付說明${NC}"
echo ""
echo "1. 前往你的 Repository:"
echo "   https://github.com/$GITHUB_USER/$REPO_NAME"
echo ""
echo "2. 點擊 'Settings' (設定)"
echo ""
echo "3. 確認 README 與發版說明都標示：downstream 官方入口是 core/overlay bootstrap + sync"
echo ""
echo "4. 後續請用 portable/bootstrap flow 與 workflow-core sync lane 建立/更新 downstream repo"
echo ""
echo -e "${BLUE}📖 其他建議：${NC}"
echo "- 編輯 Repository 描述和 Topics"
echo "- 新增 'workflow', 'ai-agent', 'core-overlay' 等 topics"
echo "- 在 About 區塊新增 Website (可用 GitHub Pages)"
echo ""
