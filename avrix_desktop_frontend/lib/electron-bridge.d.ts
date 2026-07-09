export {}

declare global {
  interface Window {
    avrix?: {
      selectDirectory: (defaultPath?: string) => Promise<string | null>
      openPath: (targetPath: string) => Promise<{ ok: boolean; error?: string }>
      getDefaultDownloadsPath: () => Promise<string>
    }
  }
}
