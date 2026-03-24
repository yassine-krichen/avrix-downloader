"use client"

import { useEffect, useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group"
import { Checkbox } from "@/components/ui/checkbox"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import {
  Download,
  FolderOpen,
  Play,
  Trash2,
  LinkIcon,
  Moon,
  Sun,
  HelpCircle,
  Info,
  Music,
  Film,
  Zap,
  Sliders,
  ChevronUp,
  ChevronDown,
  ListVideo,
  AlertCircle,
} from "lucide-react"
import { getSettings, updateSettings } from "@/lib/api/client"
import type { ErrorResponse, Quality } from "@/lib/api/types"

interface QueueItem {
  id: string
  url: string
  status: "pending" | "downloading" | "completed" | "error"
  format: string
  quality: string
  progress: number
}

function detectYouTubeUrlType(url: string): { type: "video" | "playlist" | "short" | "invalid"; icon: typeof Play } {
  if (!url.trim()) return { type: "invalid", icon: AlertCircle }

  const playlistPattern = /(?:youtube\.com\/playlist\?list=|youtu\.be\/.*[?&]list=)/i
  const shortPattern = /(?:youtube\.com\/shorts\/|youtu\.be\/[a-zA-Z0-9_-]{11}\?(?!.*list))/i
  const videoPattern = /(?:youtube\.com\/watch\?v=|youtu\.be\/)/i

  if (playlistPattern.test(url)) return { type: "playlist", icon: ListVideo }
  if (shortPattern.test(url)) return { type: "short", icon: Play }
  if (videoPattern.test(url)) return { type: "video", icon: Play }

  return { type: "invalid", icon: AlertCircle }
}

const QUALITY_OPTIONS: Array<{ value: Quality; label: string }> = [
  { value: "best", label: "Best Available" },
  { value: "2160p", label: "2160p (4K)" },
  { value: "1440p", label: "1440p" },
  { value: "1080p", label: "1080p" },
  { value: "720p", label: "720p" },
  { value: "480p", label: "480p" },
  { value: "360p", label: "360p" },
  { value: "240p", label: "240p" },
  { value: "144p", label: "144p" },
]

export default function AvrixDownloader() {
  const [theme, setTheme] = useState<"light" | "dark">("light")
  const [showAbout, setShowAbout] = useState(false)

  const [sourceUrl, setSourceUrl] = useState("")
  const [format, setFormat] = useState<"audio" | "video">("video")
  const [quality, setQuality] = useState<Quality>("best")
  const [downloadSubtitles, setDownloadSubtitles] = useState(false)
  const [embedThumbnail, setEmbedThumbnail] = useState(true)
  const [outputLocation, setOutputLocation] = useState("C:/Users/user/Downloads")
  const [maxConcurrent, setMaxConcurrent] = useState("3")
  const [activeTab, setActiveTab] = useState("current")
  const [settingsStatus, setSettingsStatus] = useState<string>("")

  const [queueItems, setQueueItems] = useState<QueueItem[]>([
    {
      id: "1",
      url: "https://youtu.be/example1",
      status: "pending",
      format: "MP4",
      quality: "best",
      progress: 0,
    },
    {
      id: "2",
      url: "https://youtu.be/example2",
      status: "downloading",
      format: "MP3",
      quality: "best",
      progress: 45,
    },
  ])

  const urlDetection = detectYouTubeUrlType(sourceUrl)

  useEffect(() => {
    const loadSettings = async () => {
      try {
        const settings = await getSettings()
        setSourceUrl(settings.last_url ?? "")
        setFormat(settings.format_type === "mp3" ? "audio" : "video")
        setQuality(settings.quality)
        setDownloadSubtitles(settings.download_subtitles)
        setEmbedThumbnail(settings.embed_thumbnail)
        setOutputLocation(settings.download_path)
        setMaxConcurrent(String(settings.max_concurrent_downloads))
      } catch {
        setSettingsStatus("Could not load settings from backend")
      }
    }

    loadSettings()
  }, [])

  const saveSettings = async () => {
    setSettingsStatus("Saving settings...")

    try {
      await updateSettings({
        last_url: sourceUrl,
        format_type: format === "audio" ? "mp3" : "mp4",
        quality,
        download_subtitles: downloadSubtitles,
        embed_thumbnail: embedThumbnail,
        download_path: outputLocation,
        max_concurrent_downloads: Number(maxConcurrent),
      })
      setSettingsStatus("Settings saved")
    } catch (error) {
      const message = (error as ErrorResponse)?.message ?? "Failed to save settings"
      setSettingsStatus(message)
    }
  }

  const pickOutputLocation = async () => {
    try {
      const electronRequire = (window as Window & { require?: (name: string) => any }).require
      const ipcRenderer = electronRequire?.("electron")?.ipcRenderer

      if (!ipcRenderer) {
        setSettingsStatus("Folder picker is only available in desktop mode")
        return
      }

      const selectedPath = await ipcRenderer.invoke("dialog:selectDirectory", outputLocation)
      if (selectedPath) {
        setOutputLocation(selectedPath)
        setSettingsStatus("Output location updated. Click Save Settings to persist.")
      }
    } catch {
      setSettingsStatus("Failed to open folder picker")
    }
  }

  const openOutputFolder = async () => {
    try {
      const electronRequire = (window as Window & { require?: (name: string) => any }).require
      const ipcRenderer = electronRequire?.("electron")?.ipcRenderer

      if (!ipcRenderer) {
        setSettingsStatus("Open Folder is only available in desktop mode")
        return
      }

      const result = await ipcRenderer.invoke("shell:openPath", outputLocation)
      if (!result?.ok) {
        setSettingsStatus(result?.error || "Could not open output folder")
      }
    } catch {
      setSettingsStatus("Failed to open output folder")
    }
  }

  const toggleTheme = () => {
    const newTheme = theme === "light" ? "dark" : "light"
    setTheme(newTheme)
    document.documentElement.classList.toggle("dark", newTheme === "dark")
  }

  const moveQueueItem = (id: string, direction: "up" | "down") => {
    const index = queueItems.findIndex((item) => item.id === id)
    if ((direction === "up" && index === 0) || (direction === "down" && index === queueItems.length - 1)) return

    const newItems = [...queueItems]
    const newIndex = direction === "up" ? index - 1 : index + 1
    newItems[index] = newItems[newIndex]
    newItems[newIndex] = queueItems[index]
    setQueueItems(newItems)
  }

  const removeQueueItem = (id: string) => {
    setQueueItems(queueItems.filter((item) => item.id !== id))
  }

  const clearFinished = () => {
    setQueueItems(queueItems.filter((item) => item.status !== "completed"))
  }

  const clearAll = () => {
    setQueueItems([])
  }

  const getStatusDisplay = (status: string) => {
    const statusMap: Record<string, { label: string; color: string }> = {
      pending: { label: "Pending", color: "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200" },
      downloading: { label: "Downloading", color: "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200" },
      completed: { label: "Completed", color: "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200" },
      error: { label: "Error", color: "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200" },
    }
    return statusMap[status] || statusMap.pending
  }

  return (
    <div className="flex flex-col bg-background text-foreground">
      {/* Header */}
      <header className="flex h-10 items-center justify-between border-b border-border px-3 gap-2">
        <div className="flex items-center gap-2">
          <div className="flex h-6 w-6 items-center justify-center rounded bg-primary">
            <span className="text-xs font-bold text-primary-foreground">A</span>
          </div>
          <span className="text-sm font-semibold">Avrix</span>
        </div>
        <div className="flex items-center gap-1">
          <Button variant="ghost" size="sm" onClick={toggleTheme} className="h-8 w-8 p-0">
            {theme === "light" ? <Moon className="h-4 w-4" /> : <Sun className="h-4 w-4" />}
          </Button>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                <HelpCircle className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem onSelect={() => setShowAbout(true)}>
                <Info className="mr-2 h-4 w-4" />
                About Avrix
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem>Documentation</DropdownMenuItem>
              <DropdownMenuItem>Keyboard Shortcuts</DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </header>

      <main className="flex-1 overflow-hidden p-3 flex flex-col">
        <div className="grid gap-3 flex-1 overflow-hidden grid-cols-[1fr,260px]">
          {/* Left: Configuration */}
          <div className="flex flex-col gap-2.5 overflow-y-auto pr-2 justify-start">
            <div className="grid grid-cols-2 gap-2">
              {/* URL Input */}
              <div className="flex flex-col gap-1.5">
                <Label className="text-xs font-medium flex items-center gap-1.5">
                  <LinkIcon className="h-3.5 w-3.5 text-primary" />
                  Source
                </Label>
                <div className="flex gap-1.5">
                  <Input
                    value={sourceUrl}
                    onChange={(e) => setSourceUrl(e.target.value)}
                    className="h-8 text-xs flex-1"
                    placeholder="YouTube URL"
                  />
                  <Button
                    variant="outline"
                    size="sm"
                    className="h-8 px-2.5 text-xs bg-transparent hover:bg-secondary flex items-center gap-1.5"
                  >
                    <urlDetection.icon className="h-3.5 w-3.5" />
                    <span className="capitalize">
                      {urlDetection.type === "invalid" ? "Invalid" : urlDetection.type}
                    </span>
                  </Button>
                </div>
              </div>

              {/* Output Location */}
              <div className="flex flex-col gap-1.5">
                <Label className="text-xs font-medium flex items-center gap-1.5">
                  <FolderOpen className="h-3.5 w-3.5 text-primary" />
                  Output
                </Label>
                <div className="flex gap-1.5">
                  <Input
                    value={outputLocation}
                    readOnly
                    className="h-8 text-xs flex-1 truncate bg-muted cursor-not-allowed"
                  />
                  <Button
                    variant="outline"
                    size="sm"
                    className="h-8 px-3 text-xs bg-transparent hover:bg-secondary"
                    onClick={pickOutputLocation}
                  >
                    <FolderOpen className="h-3.5 w-3.5" />
                  </Button>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-3 gap-2">
              {/* Format */}
              <div className="rounded-lg border border-border bg-card p-2.5">
                <Label className="text-xs font-medium flex items-center gap-1.5 mb-2">
                  {format === "video" ? (
                    <Film className="h-3.5 w-3.5 text-primary" />
                  ) : (
                    <Music className="h-3.5 w-3.5 text-primary" />
                  )}
                  Format
                </Label>
                <RadioGroup value={format} onValueChange={setFormat}>
                  <div className="flex items-center space-x-2">
                    <RadioGroupItem value="video" id="video" className="h-3 w-3" />
                    <Label htmlFor="video" className="cursor-pointer text-xs font-normal">
                      Video (MP4)
                    </Label>
                  </div>
                  <div className="flex items-center space-x-2">
                    <RadioGroupItem value="audio" id="audio" className="h-3 w-3" />
                    <Label htmlFor="audio" className="cursor-pointer text-xs font-normal">
                      Audio (MP3)
                    </Label>
                  </div>
                </RadioGroup>
              </div>

              {/* Quality */}
              <div className="rounded-lg border border-border bg-card p-2.5">
                <Label htmlFor="quality" className="text-xs font-medium flex items-center gap-1.5 mb-2">
                  <Zap className="h-3.5 w-3.5 text-primary" />
                  Quality
                </Label>
                <Select value={quality} onValueChange={setQuality}>
                  <SelectTrigger id="quality" className="h-7 text-xs">
                    <SelectValue placeholder="Select quality" />
                  </SelectTrigger>
                  <SelectContent>
                    {QUALITY_OPTIONS.map((option) => (
                      <SelectItem key={option.value} value={option.value}>
                        {option.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* Options */}
              <div className="rounded-lg border border-border bg-card p-2.5">
                <Label className="text-xs font-medium flex items-center gap-1.5 mb-2">
                  <Sliders className="h-3.5 w-3.5 text-primary" />
                  Options
                </Label>
                <div className="space-y-1">
                  <div className="flex items-center space-x-2">
                    <Checkbox
                      id="subtitles"
                      checked={downloadSubtitles}
                      onCheckedChange={(checked) => setDownloadSubtitles(checked as boolean)}
                      className="h-3.5 w-3.5"
                    />
                    <Label htmlFor="subtitles" className="cursor-pointer text-xs font-normal">
                      Subtitles
                    </Label>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Checkbox
                      id="thumbnail"
                      checked={embedThumbnail}
                      onCheckedChange={(checked) => setEmbedThumbnail(checked as boolean)}
                      className="h-3.5 w-3.5"
                    />
                    <Label htmlFor="thumbnail" className="cursor-pointer text-xs font-normal">
                      Thumbnail
                    </Label>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Right: Download Status Panel */}
          <div className="flex flex-col overflow-hidden">
            <Tabs value={activeTab} onValueChange={setActiveTab} className="flex h-full flex-col">
              <TabsList className="grid w-full grid-cols-2 h-8">
                <TabsTrigger value="current" className="text-xs">
                  Current
                </TabsTrigger>
                <TabsTrigger value="queue" className="text-xs">
                  Queue ({queueItems.length})
                </TabsTrigger>
              </TabsList>

              <TabsContent value="current" className="mt-2 flex-1 overflow-auto">
                <div className="rounded-lg border border-border bg-card p-2.5 h-full flex flex-col">
                  {/* Thumbnail and info with progress side by side */}
                  <div className="flex gap-2.5">
                    {/* Thumbnail - 30% width */}
                    <div className="w-[30%] aspect-video rounded bg-muted flex items-center justify-center flex-shrink-0">
                      <Play className="h-6 w-6 text-muted-foreground/40" />
                    </div>

                    {/* Info and Progress section */}
                    <div className="flex-1 flex flex-col justify-between py-1">
                      <div>
                        <p className="text-xs font-semibold text-foreground">Ready to Download</p>
                        <p className="text-[10px] text-muted-foreground mt-0.5">No video selected</p>
                      </div>
                      <div className="grid grid-cols-3 gap-1.5 mb-2.5">
                        <div>
                          <p className="text-[9px] text-muted-foreground uppercase tracking-wide">Speed</p>
                          <p className="text-xs font-semibold mt-0.5">--</p>
                        </div>
                        <div>
                          <p className="text-[9px] text-muted-foreground uppercase tracking-wide">Size</p>
                          <p className="text-xs font-semibold mt-0.5">--</p>
                        </div>
                        <div>
                          <p className="text-[9px] text-muted-foreground uppercase tracking-wide">ETA</p>
                          <p className="text-xs font-semibold mt-0.5">--</p>
                        </div>
                      </div>

                      {/* Progress bar */}
                      <div>
                        <div className="flex items-center justify-between mb-1">
                          <p className="text-xs font-medium">Progress</p>
                          <p className="text-xs text-muted-foreground">0%</p>
                        </div>
                        <div className="h-1.5 w-full rounded-full bg-muted overflow-hidden">
                          <div className="h-full rounded-full bg-primary" style={{ width: "0%" }} />
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </TabsContent>

              {/* Queue tab */}
              <TabsContent value="queue" className="mt-2 flex-1 overflow-hidden flex flex-col">
                <div className="rounded-lg border border-border bg-card overflow-hidden flex flex-col h-full">
                  <div className="border-b border-border p-2.5 flex items-center justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <Label htmlFor="concurrent" className="text-xs font-medium whitespace-nowrap">
                        Concurrent:
                      </Label>
                      <Select value={maxConcurrent} onValueChange={setMaxConcurrent}>
                        <SelectTrigger id="concurrent" className="h-7 w-20 text-xs">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {Array.from({ length: 10 }, (_, i) => (
                            <SelectItem key={i + 1} value={String(i + 1)}>
                              {i + 1}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="flex items-center gap-1.5 ml-auto">
                      <Button
                        size="sm"
                        variant="outline"
                        className="h-7 px-2 text-xs bg-transparent hover:bg-secondary"
                        onClick={clearFinished}
                      >
                        Clear Finished
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        className="h-7 px-2 text-xs bg-transparent hover:bg-secondary disabled:opacity-50 disabled:cursor-not-allowed"
                        onClick={clearAll}
                        disabled={queueItems.length === 0}
                      >
                        Clear All
                      </Button>
                    </div>
                  </div>

                  {/* Queue items */}
                  <div className="divide-y divide-border overflow-auto flex-1">
                    {queueItems.length > 0 ? (
                      queueItems.map((item) => {
                        const statusDisplay = getStatusDisplay(item.status)
                        return (
                          <div key={item.id} className="p-2 hover:bg-muted/50 transition-colors">
                            <div className="flex items-center justify-between gap-2">
                              <div className="min-w-0 flex-1">
                                <p className="truncate text-xs font-medium">{item.url}</p>
                                <div className="mt-1 flex items-center gap-1.5 text-[10px] text-muted-foreground">
                                  <span>{item.format}</span>
                                  <span>•</span>
                                  <span>{item.quality}</span>
                                  <span>•</span>
                                  <span className={`px-2 py-0.5 rounded text-[9px] font-medium ${statusDisplay.color}`}>
                                    {statusDisplay.label}
                                  </span>
                                </div>
                              </div>
                              <div className="flex items-center gap-1">
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  className="h-6 w-6 p-0 hover:bg-muted"
                                  onClick={() => moveQueueItem(item.id, "up")}
                                >
                                  <ChevronUp className="h-3.5 w-3.5" />
                                </Button>
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  className="h-6 w-6 p-0 hover:bg-muted"
                                  onClick={() => moveQueueItem(item.id, "down")}
                                >
                                  <ChevronDown className="h-3.5 w-3.5" />
                                </Button>
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  className="h-6 w-6 p-0 hover:bg-destructive/10 hover:text-destructive"
                                  onClick={() => removeQueueItem(item.id)}
                                >
                                  <Trash2 className="h-3.5 w-3.5" />
                                </Button>
                              </div>
                            </div>
                          </div>
                        )
                      })
                    ) : (
                      <div className="flex h-full items-center justify-center">
                        <p className="text-xs text-muted-foreground">Queue is empty</p>
                      </div>
                    )}
                  </div>

                  <div className="border-t border-border p-2.5 flex gap-2 justify-end">
                    <Button size="sm" className="h-7 px-3 text-xs font-medium">
                      <Play className="mr-1 h-3.5 w-3.5" />
                      Start Queue
                    </Button>
                    <Button size="sm" variant="outline" className="h-7 px-3 text-xs bg-transparent hover:bg-secondary">
                      Stop Queue
                    </Button>
                  </div>
                </div>
              </TabsContent>
            </Tabs>
          </div>
        </div>

        <div className="flex gap-2 pt-3 border-t border-border">
          <Button size="sm" variant="outline" className="h-8 px-3 text-xs bg-transparent hover:bg-secondary" onClick={saveSettings}>
            Save Settings
          </Button>
          <Button size="sm" className="h-8 px-3 text-xs font-medium">
            <Download className="mr-1 h-3.5 w-3.5" />
            Start Download
          </Button>
          <Button size="sm" variant="outline" className="h-8 px-3 text-xs bg-transparent hover:bg-secondary">
            Add to Queue
          </Button>
          <Button
            size="sm"
            className="h-8 px-3 text-xs bg-red-600 hover:bg-red-700 text-white font-medium border border-red-600 hover:border-red-700 ml-auto"
          >
            Cancel
          </Button>
          <Button
            variant="outline"
            size="sm"
            className="h-8 px-3 text-xs bg-transparent hover:bg-secondary"
            onClick={openOutputFolder}
          >
            <FolderOpen className="mr-1 h-3 w-3" />
            Open Folder
          </Button>
        </div>

        {settingsStatus ? <p className="pt-2 text-xs text-muted-foreground">{settingsStatus}</p> : null}
      </main>

      {/* About Dialog */}
      <Dialog open={showAbout} onOpenChange={setShowAbout}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <div className="flex items-center gap-3 mb-2">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary">
                <span className="text-lg font-bold text-primary-foreground">A</span>
              </div>
              <div>
                <DialogTitle>Avrix</DialogTitle>
                <DialogDescription className="text-xs">Version 1.0.0</DialogDescription>
              </div>
            </div>
          </DialogHeader>
          <div className="space-y-4">
            <p className="text-sm text-foreground">Professional video & audio download manager for YouTube</p>
            <div className="space-y-2">
              <h4 className="text-sm font-semibold">Features</h4>
              <ul className="text-xs text-muted-foreground space-y-1 ml-4">
                <li>• Download videos and audio from YouTube</li>
                <li>• Support for playlists and individual videos</li>
                <li>• Multiple quality options (144p - 4K)</li>
                <li>• Concurrent downloads with queue management</li>
                <li>• Subtitle and thumbnail embedding</li>
                <li>• Light and dark theme support</li>
              </ul>
            </div>
            <p className="text-xs text-muted-foreground border-t border-border pt-4">
              For educational and learning purposes only. Respect copyright and terms of service.
            </p>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  )
}
