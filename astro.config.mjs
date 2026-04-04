// @ts-check
// Astro設定ファイル - The Pen Archive
// サイトマップ・MDX・多言語（i18n）を統合
import { defineConfig } from 'astro/config';
import sitemap from '@astrojs/sitemap';
import mdx from '@astrojs/mdx';

export default defineConfig({
  // 本番サイトのURL
  site: 'https://thepenarchive.com',

  // 使用するインテグレーション
  integrations: [
    sitemap(),  // サイトマップ自動生成
    mdx(),      // MDXファイルサポート
  ],

  // 多言語（i18n）設定: 英語メイン、日本語サブ
  i18n: {
    defaultLocale: 'en',        // デフォルト言語: 英語
    locales: ['en', 'ja'],      // 対応言語: 英語 と 日本語
    routing: {
      prefixDefaultLocale: false,  // 英語は / のまま、日本語は /ja/ プレフィックス
    },
  },
});
