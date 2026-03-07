import { defineConfig } from 'vitepress'

// https://vitepress.dev/reference/site-config
export default defineConfig({
  title: 'oh-my-kanban',
  description: 'Plane + Claude Code 자동 WI 연동 플러그인',

  // 한국어 기본, 영어 지원
  locales: {
    root: {
      label: '한국어',
      lang: 'ko',
      link: '/ko/',
      themeConfig: {
        nav: [
          { text: '홈', link: '/ko/' },
          { text: '시작하기', link: '/ko/getting-started' },
          { text: 'CLI 레퍼런스', link: '/ko/cli-reference' },
          { text: '설정', link: '/ko/configuration' },
        ],
        sidebar: {
          '/ko/': [
            {
              text: '소개',
              items: [
                { text: 'oh-my-kanban이란?', link: '/ko/' },
                { text: '시작하기', link: '/ko/getting-started' },
              ],
            },
            {
              text: '사용법',
              items: [
                { text: 'CLI 명령어', link: '/ko/cli-reference' },
                { text: '스킬 목록', link: '/ko/skills' },
                { text: '설정 레퍼런스', link: '/ko/configuration' },
              ],
            },
            {
              text: '고급',
              items: [
                { text: 'Task Format 가이드', link: '/ko/task-format' },
                { text: '기록 모드', link: '/ko/recording-modes' },
                { text: 'Preset 시스템', link: '/ko/presets' },
              ],
            },
          ],
        },
        socialLinks: [
          { icon: 'github', link: 'https://github.com/ej31/oh-my-kanban' },
        ],
        footer: {
          message: 'MIT 라이선스로 배포됩니다.',
          copyright: 'Copyright © 2026 oh-my-kanban contributors',
        },
      },
    },
    en: {
      label: 'English',
      lang: 'en',
      link: '/en/',
      themeConfig: {
        nav: [
          { text: 'Home', link: '/en/' },
          { text: 'Getting Started', link: '/en/getting-started' },
          { text: 'CLI Reference', link: '/en/cli-reference' },
          { text: 'Configuration', link: '/en/configuration' },
        ],
        sidebar: {
          '/en/': [
            {
              text: 'Introduction',
              items: [
                { text: 'What is oh-my-kanban?', link: '/en/' },
                { text: 'Getting Started', link: '/en/getting-started' },
              ],
            },
            {
              text: 'Usage',
              items: [
                { text: 'CLI Commands', link: '/en/cli-reference' },
                { text: 'Skills', link: '/en/skills' },
                { text: 'Configuration Reference', link: '/en/configuration' },
              ],
            },
          ],
        },
        socialLinks: [
          { icon: 'github', link: 'https://github.com/ej31/oh-my-kanban' },
        ],
      },
    },
  },

  themeConfig: {
    // 공통 테마 설정
    search: {
      provider: 'local',
    },
  },

  // docs/**의 변경만 배포 트리거 (GitHub Actions path filter와 연동)
  srcDir: '.',
  outDir: '.vitepress/dist',
})
