export default {
  locales: [
    {
      name: 'English',
      code: 'en',
      iso: 'en-CA',
      file: 'en'
    },
    {
      name: 'བོད་ཡིག',
      code: 'bo',
      iso: 'bo-CN',
      file: 'bo'
    },
    {
      name: '中文',
      code: 'zh',
      iso: 'zh-CN',
      file: 'zh'
    },
    {
      name: 'Français',
      code: 'fr',
      iso: 'fr-CA',
      file: 'fr'
    },
    {
      name: 'Deutsch',
      code: 'de',
      iso: 'de-DE',
      file: 'de'
    }
  ],
  lazy: true,
  langDir: 'i18n/',
  defaultLocale: 'en',
  vueI18n: {
    fallbackLocale: 'en'
  },
  detectBrowserLanguage: {
    useCookie: true,
    cookieKey: 'i18n_redirected',
    onlyOnRoot: true // for SEO purposes
  }
}

