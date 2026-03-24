const { app, BrowserWindow, ipcMain, dialog, shell } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const http = require('http');

let mainWindow;
let pythonProcess;
const API_PORT = 8000;

ipcMain.handle('dialog:selectDirectory', async (_event, defaultPath) => {
  const result = await dialog.showOpenDialog({
    properties: ['openDirectory'],
    defaultPath: typeof defaultPath === 'string' && defaultPath ? defaultPath : undefined,
  });

  if (result.canceled || result.filePaths.length === 0) {
    return null;
  }

  return result.filePaths[0];
});

ipcMain.handle('shell:openPath', async (_event, targetPath) => {
  if (typeof targetPath !== 'string' || !targetPath.trim()) {
    return { ok: false, error: 'Invalid path' };
  }

  const openError = await shell.openPath(targetPath);
  if (openError) {
    return { ok: false, error: openError };
  }

  return { ok: true };
});

function waitForBackendReady(timeoutMs = 10000) {
  const start = Date.now();

  return new Promise((resolve, reject) => {
    const probe = () => {
      const req = http.get(`http://127.0.0.1:${API_PORT}/health/ready`, (res) => {
        if (res.statusCode === 200) {
          resolve();
          return;
        }
        retryOrFail();
      });

      req.on('error', retryOrFail);
      req.end();
    };

    const retryOrFail = () => {
      if (Date.now() - start >= timeoutMs) {
        reject(new Error('Backend readiness timeout'));
        return;
      }
      setTimeout(probe, 250);
    };

    probe();
  });
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false, // For simple dev, consider enabling for prod
    },
  });

  // In development, load from Next.js dev server
  // In production, load from static file
  const isDev = process.env.NODE_ENV === 'development';
  
  if (isDev) {
    mainWindow.loadURL('http://localhost:3000');
    mainWindow.webContents.openDevTools();
  } else {
    mainWindow.loadFile(path.join(__dirname, '../avrix_desktop_frontend/out/index.html'));
  }

  mainWindow.on('closed', function () {
    mainWindow = null;
  });
}

function startPythonServer() {
  const backendRoot = path.join(__dirname, '../avrix_sidecar_backend');
  
  pythonProcess = spawn('python', ['-m', 'app.main'], {
    cwd: backendRoot,
    env: {
      ...process.env,
      PYTHONPATH: backendRoot,
    }
  });

  pythonProcess.stdout.on('data', (data) => {
    console.log(`Python: ${data}`);
  });

  pythonProcess.stderr.on('data', (data) => {
    console.error(`Python Error: ${data}`);
  });
}

app.on('ready', () => {
  startPythonServer();

  waitForBackendReady()
    .then(() => createWindow())
    .catch((error) => {
      console.error(`Backend startup error: ${error.message}`);
      app.quit();
    });
});

app.on('window-all-closed', function () {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('quit', () => {
  if (pythonProcess) {
    pythonProcess.kill();
  }
});

app.on('activate', function () {
  if (mainWindow === null) {
    createWindow();
  }
});
