"""
generate-articles.py — Claude APIを使って記事を自動生成するスクリプト

使い方:
  python scripts/generate-articles.py --type guide --limit 2 --lang en
  python scripts/generate-articles.py --type comparison --limit 1 --lang ja

引数:
  --type  : 記事カテゴリ (review/ink/nib/comparison/guide/beginner)
  --limit : 生成する記事数 (デフォルト: 2)
  --lang  : 言語 (en/ja、デフォルト: en)
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Anthropic SDKのインポート（インストールされていない場合のエラーハンドリング）
try:
    import anthropic
except ImportError:
    print("Error: anthropic パッケージが必要です。")
    print("  pip install anthropic")
    sys.exit(1)


def load_json(filepath: str) -> list | dict:
    """JSONファイルを読み込むヘルパー関数"""
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def get_unused_keywords(keywords_path: str, articles_path: str, category: str) -> list:
    """
    まだ記事が生成されていないキーワードを取得する。
    既存の記事のスラッグと比較して、未使用のものだけを返す。
    """
    keywords_data = load_json(keywords_path)
    keywords = keywords_data.get(category, [])

    # 既存の記事ファイル名を取得
    existing_slugs = set()
    articles_dir = Path(articles_path)
    if articles_dir.exists():
        for f in articles_dir.glob("*.md"):
            existing_slugs.add(f.stem)  # 拡張子なしのファイル名

    # 未使用のキーワードだけ返す
    unused = [kw for kw in keywords if kw["slug"] not in existing_slugs]
    return unused


def generate_article(client: anthropic.Anthropic, keyword: dict, lang: str,
                     pens_data: list, inks_data: list, brands_data: list) -> str:
    """
    Claude APIを呼び出して記事を生成する。
    万年筆・インク・ブランドデータをコンテキストとして渡す。
    """
    # 言語に応じたプロンプト
    if lang == "ja":
        lang_instruction = """
記事は日本語で書いてください。
ターゲット読者は日本の万年筆愛好家です。
"""
    else:
        lang_instruction = """
Write the article in English.
Target audience is international fountain pen enthusiasts and writers.
"""

    # システムプロンプト
    system_prompt = f"""You are an expert fountain pen reviewer and writing instrument journalist for The Pen Archive (thepenarchive.com).
You write authoritative, detailed, and engaging content about fountain pens, inks, and nibs.
Your tone is knowledgeable but accessible — like a seasoned collector explaining to an eager newcomer.
{lang_instruction}

IMPORTANT: Output ONLY the Markdown content with frontmatter. No additional commentary."""

    # ユーザープロンプト（記事生成指示）
    user_prompt = f"""Generate a complete article for the keyword: "{keyword['keyword']}"
Slug: {keyword['slug']}
Category: {keyword['category']}

Use the following data for accurate information:

PENS DATA (first 10):
{json.dumps(pens_data[:10], indent=2, ensure_ascii=False)[:3000]}

INKS DATA:
{json.dumps(inks_data, indent=2, ensure_ascii=False)[:2000]}

BRANDS DATA:
{json.dumps(brands_data, indent=2, ensure_ascii=False)[:2000]}

Requirements:
1. Start with YAML frontmatter:
   - title: Compelling, SEO-optimized title
   - description: 150-160 char meta description
   - category: "{keyword['category']}"
   - tags: Relevant tags array
   - publishedAt: "{datetime.now().strftime('%Y-%m-%d')}"
   - articleType: "guide" or "review" or "comparison" or "listicle"

2. Article body:
   - 800-1500 words
   - Use ## for H2, ### for H3
   - Include specific pen recommendations with prices
   - Reference actual pens from the data
   - Natural, conversational tone
   - Practical advice based on real-world usage
   - No fluff or filler content
"""

    # Claude API呼び出し
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4000,
        messages=[
            {"role": "user", "content": user_prompt}
        ],
        system=system_prompt,
    )

    return message.content[0].text


def save_article(content: str, slug: str, articles_path: str) -> str:
    """記事をMarkdownファイルとして保存する"""
    filepath = os.path.join(articles_path, f"{slug}.md")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    return filepath


def main():
    # コマンドライン引数のパース
    parser = argparse.ArgumentParser(description="The Pen Archive 記事自動生成スクリプト")
    parser.add_argument("--type", type=str, default="guide",
                        choices=["review", "ink", "nib", "comparison", "guide", "beginner"],
                        help="記事カテゴリ（デフォルト: guide）")
    parser.add_argument("--limit", type=int, default=2,
                        help="生成する記事数（デフォルト: 2）")
    parser.add_argument("--lang", type=str, default="en",
                        choices=["en", "ja"],
                        help="言語（デフォルト: en）")
    args = parser.parse_args()

    # APIキーの確認
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY 環境変数が設定されていません。")
        sys.exit(1)

    # パスの設定
    project_root = Path(__file__).parent.parent
    keywords_path = project_root / "src" / "data" / "keywords.json"
    articles_path = project_root / "src" / "content" / "articles"
    pens_path = project_root / "src" / "data" / "pens.json"
    inks_path = project_root / "src" / "data" / "inks.json"
    brands_path = project_root / "src" / "data" / "brands.json"

    # データの読み込み
    pens_data = load_json(str(pens_path))
    inks_data = load_json(str(inks_path))
    brands_data = load_json(str(brands_path))

    # 未使用キーワードの取得
    unused_keywords = get_unused_keywords(
        str(keywords_path), str(articles_path), args.type
    )

    if not unused_keywords:
        print(f"カテゴリ '{args.type}' の未使用キーワードがありません。")
        sys.exit(0)

    # 生成数を制限
    keywords_to_generate = unused_keywords[:args.limit]

    print(f"=== The Pen Archive 記事生成 ===")
    print(f"カテゴリ: {args.type}")
    print(f"言語: {args.lang}")
    print(f"生成数: {len(keywords_to_generate)}")
    print()

    # Anthropicクライアントの初期化
    client = anthropic.Anthropic(api_key=api_key)

    # 各キーワードについて記事を生成
    for i, keyword in enumerate(keywords_to_generate, 1):
        print(f"[{i}/{len(keywords_to_generate)}] 生成中: {keyword['keyword']}...")

        try:
            # 記事を生成
            content = generate_article(
                client, keyword, args.lang,
                pens_data, inks_data, brands_data
            )

            # ファイルとして保存
            filepath = save_article(content, keyword["slug"], str(articles_path))
            print(f"  → 保存完了: {filepath}")

        except Exception as e:
            print(f"  → エラー: {e}")
            continue

    print()
    print("=== 完了 ===")


if __name__ == "__main__":
    main()
