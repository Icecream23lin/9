const { app, BrowserWindow, ipcMain, dialog } = require("electron");
const { spawn } = require("child_process");
const path = require("path");
const fs = require("fs");
const { checkBackend, retryWithDelay } = require("./helper.js");
let backendProcess;
let win;

app.setAppUserModelId("Insight Generation Tool");
app.setPath("userData", path.join(app.getPath("temp"), ".wil-insight-tool"));

const createWindow = () => {
  win = new BrowserWindow({
    width: 800,
    height: 600,
    show: false,
    autoHideMenuBar: true,
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
      preload: path.join(__dirname, "preload.js"),
    },
  });

  // Load Vite dev server during development
  win.loadURL("http://localhost:5173");
  // prod load
  // win.loadFile(path.join(__dirname, '../frontend/dist/index.html'));
  win.webContents.on("did-finish-load", () => {
    win.show();
  });
};

app.whenReady().then(async () => {
  // start backend process here
  backendProcess = spawn("python", ["backend/run.py"], {
    stdio: "inherit",
    windowsHide: true,
  });

  ipcMain.handle("backend-port-channel", async () => {
    return 5050;
  });

  ipcMain.handle("download-dialog", async (event, data) => {
    const res = await dialog.showSaveDialog(win, {
      defaultPath: `${data.file_name}.zip`,
      filters: [
        {
          name: "ZIP Files",
          extensions: ["zip"],
        },
      ],
    });
    if (!res.canceled && res.filePath) {
      try {
        fs.writeFileSync(res.filePath, Buffer.from(data.file));
        return true;
      } catch (e) {
        console.log(e);
        return false;
      }
    }
    return false;
  });

  // wait for backend and create window
  try {
    await retryWithDelay(
      () => checkBackend("http://localhost:5050/api/health"),
      10,
      500
    );
    createWindow();
  } catch (err) {
    dialog.showErrorBox("Backend Error", "Backend failed to start.");
    console.error(err);
    app.quit();
  }
});

app.on("activate", () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") {
    if (backendProcess && !backendProcess.killed) {
      backendProcess.kill("SIGTERM");
      console.log("Backend process killed");
    }

    app.quit();
  }
});
