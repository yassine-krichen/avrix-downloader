const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('avrix', {
  selectDirectory: (defaultPath) => ipcRenderer.invoke('dialog:selectDirectory', defaultPath),
  openPath: (targetPath) => ipcRenderer.invoke('shell:openPath', targetPath),
  getDefaultDownloadsPath: () => ipcRenderer.invoke('app:getDefaultDownloadsPath'),
});
