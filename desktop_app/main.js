const { app, BrowserWindow } = require('electron');
const path = require('path');
const { spawn, execSync } = require('child_process');

let mainWindow;
let flaskProcess;
let traderProcess;
let viteProcess;

/**
 * Kill any stale process occupying a given port.
 * Prevents "port already in use" errors from previous unclean shutdowns.
 */
function freePort(port) {
    try {
        const result = execSync(
            `netstat -ano | findstr ":${port}" | findstr "LISTENING"`,
            { encoding: 'utf-8', timeout: 5000 }
        );
        const lines = result.trim().split('\n');
        const pids = new Set();
        for (const line of lines) {
            const parts = line.trim().split(/\s+/);
            const pid = parseInt(parts[parts.length - 1], 10);
            if (pid && pid !== process.pid) pids.add(pid);
        }
        for (const pid of pids) {
            console.log(`[CLEANUP] Killing stale process on port ${port} (PID: ${pid})`);
            try { execSync(`taskkill /PID ${pid} /T /F`, { timeout: 5000 }); } catch (_) {}
        }
    } catch (_) {
        // No process on port — nothing to do
    }
}

function createWindow() {
    mainWindow = new BrowserWindow({
        width: 1400,
        height: 900,
        webPreferences: {
            nodeIntegration: true,
            contextIsolation: false
        },
        title: "Sovereign AI Trading Terminal",
        backgroundColor: '#030305', // Matches the God-level CSS
        autoHideMenuBar: true,
    });

    // Launch the backend (dashboard_server.py is the new FastAPI)
    const rootDir = path.join(__dirname, '..');
    const pythonExecutable = 'C:\\Users\\satya\\AppData\\Local\\Programs\\Python\\Python312\\python.exe';

    // Force UTF-8 encoding for all Python subprocesses (prevents charmap codec crash on Windows)
    const pythonEnv = { ...process.env, PYTHONIOENCODING: 'utf-8', PYTHONUTF8: '1' };

    // Clean up stale processes from previous unclean shutdowns
    freePort(8000);
    freePort(5173);

    flaskProcess = spawn(pythonExecutable, ['dashboard_server.py'], {
        cwd: rootDir,
        detached: false,
        shell: true,
        env: pythonEnv
    });

    flaskProcess.stdout.on('data', (data) => {
        console.log(`Backend stdout: ${data}`);
    });

    flaskProcess.stderr.on('data', (data) => {
        console.error(`Backend stderr: ${data}`);
    });

    // Launch the core trading engine
    traderProcess = spawn(pythonExecutable, ['auto_trader.py'], {
        cwd: rootDir,
        detached: false,
        shell: true,
        env: pythonEnv
    });

    traderProcess.stdout.on('data', (data) => {
        console.log(`Trader stdout: ${data}`);
    });

    traderProcess.stderr.on('data', (data) => {
        console.error(`Trader stderr: ${data}`);
    });

    // Launch the Native Vite Hot-Reloading Frontend
    const frontendDir = path.join(rootDir, 'frontend');
    viteProcess = spawn('npm', ['run', 'dev'], {
        cwd: frontendDir,
        detached: false,
        shell: true
    });

    viteProcess.stdout.on('data', (data) => {
        console.log(`Vite stdout: ${data}`);
    });
    viteProcess.stderr.on('data', (data) => {
        console.error(`Vite stderr: ${data}`);
    });

    // Give the servers time to boot up and serve the interactive React build
    const loadFrontend = () => {
        mainWindow.loadURL('http://localhost:5173/')
            .catch(e => {
                console.log('Vite not ready yet, retrying in 2 seconds...');
                setTimeout(loadFrontend, 2000);
            });
    };
    
    setTimeout(loadFrontend, 3000);

    mainWindow.on('closed', function () {
        mainWindow = null;
    });
}

app.whenReady().then(createWindow);

app.on('window-all-closed', function () {
    if (process.platform !== 'darwin') app.quit();
});

const { exec } = require('child_process');
app.on('will-quit', () => {
    if (flaskProcess && flaskProcess.pid) {
        exec(`taskkill /pid ${flaskProcess.pid} /T /F`);
    }
    if (traderProcess && traderProcess.pid) {
        exec(`taskkill /pid ${traderProcess.pid} /T /F`);
    }
    if (viteProcess && viteProcess.pid) {
        exec(`taskkill /pid ${viteProcess.pid} /T /F`);
    }
});
