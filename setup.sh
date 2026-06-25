#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$SCRIPT_DIR/venv"

find_python() {
    for cmd in python3.11 python3 python; do
        if command -v "$cmd" &>/dev/null; then
            if "$cmd" -c "import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)" 2>/dev/null; then
                echo "$cmd"
                return 0
            fi
        fi
    done
    return 1
}

install_python() {
    local os
    os="$(uname)"
    if [[ "$os" == "Linux" ]]; then
        if command -v apt-get &>/dev/null; then
            echo "sudo apt-get を使って Python 3.11 をインストールします..."
            sudo apt-get update -qq
            sudo apt-get install -y python3.11 python3.11-venv
        else
            echo "エラー: このLinuxディストリビューションでの自動インストールはサポートされていません。" >&2
            echo "Python 3.11 を手動でインストールしてください: https://www.python.org/downloads/" >&2
            exit 1
        fi
    elif [[ "$os" == "Darwin" ]]; then
        if command -v brew &>/dev/null; then
            echo "Homebrew を使って Python 3.11 をインストールします..."
            brew install python@3.11
        else
            echo "エラー: Homebrew が見つかりません。" >&2
            echo "https://brew.sh/ から Homebrew をインストールするか、Python 3.11 を手動でインストールしてください。" >&2
            exit 1
        fi
    else
        echo "エラー: このOSでの自動インストールはサポートされていません。" >&2
        echo "Python 3.11 を手動でインストールしてください: https://www.python.org/downloads/" >&2
        exit 1
    fi
}

echo "=== employee-stock-analyzer セットアップ ==="
echo ""

PYTHON=""
if ! PYTHON="$(find_python)"; then
    echo "Python 3.11 以上が見つかりませんでした。"
    read -rp "Python 3.11 をインストールしますか？ [y/N]: " answer
    if [[ "${answer,,}" == "y" ]]; then
        install_python
        if ! PYTHON="$(find_python)"; then
            echo "エラー: インストール後も Python 3.11 が見つかりません。" >&2
            exit 1
        fi
    else
        echo "エラー: Python 3.11 以上が必要です。セットアップを中止しました。" >&2
        exit 1
    fi
fi

echo "Python: $("$PYTHON" --version)"

if [[ -d "$VENV_DIR" ]]; then
    echo "venv/ が既に存在するためスキップします。"
else
    echo "venv/ を作成しています..."
    "$PYTHON" -m venv "$VENV_DIR"
fi

echo "pip / setuptools を更新しています..."
"$VENV_DIR/bin/pip" install --quiet --upgrade pip setuptools

echo "パッケージをインストールしています..."
"$VENV_DIR/bin/pip" install --quiet -e "$SCRIPT_DIR"

echo ""
echo "=== セットアップ完了 ==="
echo ""
echo "使い方:"
echo "  # venv を有効化して使う場合"
echo "  source venv/bin/activate"
echo "  stock --help"
echo ""
echo "  # 直接実行する場合"
echo "  venv/bin/stock --help"
