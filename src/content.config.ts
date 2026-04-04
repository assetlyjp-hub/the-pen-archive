// content.config.ts - Astro v6 Content Layer API の設定
// glob loader を使って Markdown 記事を読み込む

import { defineCollection, z } from 'astro:content';
import { glob } from 'astro/loaders';

// Magazine記事コレクションの定義
const articles = defineCollection({
  // glob loader で src/content/articles/ 内の .md ファイルを読み込む
  loader: glob({ pattern: '**/*.md', base: './src/content/articles' }),

  // 記事のフロントマターのスキーマ（バリデーション）
  schema: z.object({
    title: z.string(),                    // 記事タイトル
    description: z.string(),              // 概要（SEO用）
    category: z.enum([                    // 記事カテゴリ
      'review',       // ペンレビュー
      'ink',          // インク関連
      'nib',          // ペン先関連
      'comparison',   // 比較記事
      'guide',        // ガイド・ハウツー
      'beginner',     // 初心者向け
    ]),
    tags: z.array(z.string()).optional(), // タグ（任意）
    publishedAt: z.string(),             // 公開日（YYYY-MM-DD）
    updatedAt: z.string().optional(),    // 更新日（任意）
    relatedPens: z.array(z.string()).optional(), // 関連するペンのID
    articleType: z.enum([                // 記事タイプ
      'guide',       // ガイド
      'review',      // レビュー
      'comparison',  // 比較
      'listicle',    // リスト記事
    ]),
  }),
});

// コレクションをエクスポート
export const collections = { articles };
