const { app, BrowserWindow } = require("electron");
const path = require("path");
const { spawn } = require("child_process");

let mainWindow = null;
let serverProc = null;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1100,
    height: 750,
    minWidth: 800,
    minHeight: 600,
    title: "Piper AI Tiếng Việt - Ứng Dụng Đọc Truyện Desktop",
    backgroundColor: "#0f172a",
    autoHideMenuBar: true,
    icon: path.join(__dirname, "public", "favicon.ico"),
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
    },
  });

  // Load local server inside native Electron window
  mainWindow.loadURL("http://localhost:3000");

  mainWindow.on("closed", () => {
    mainWindow = null;
  });
}

function startNextServerAndWindow() {
  // Spawn Next.js server locally
  serverProc = spawn("npx", ["next", "dev", "-p", "3000"], {
    cwd: __dirname,
    shell: true,
    stdio: "pipe",
  });

  // Wait for server to be ready then create native desktop window
  setTimeout(() => {
    createWindow();
  }, 4000);
}

app.whenReady().then(() => {
  startNextServerAndWindow();

  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on("window-all-closed", () => {
  if (serverProc) {
    try {
      serverProc.kill();
    } catch {}
  }
  if (process.platform !== "darwin") {
    app.quit();
  }
});
